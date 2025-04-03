import machine
import json
import time

from math import sqrt

import usb.device
from usb.device.cdc import CDCInterface


# default lambda functions for generating 
_dg = lambda f: '%s()' % f
_dr = lambda r: r
_d = (_dg, _dr)



class EmptyEpsilonInterface:
    # key: function name
    # value: (
    #    lambda(function name, *optargs) -> api function call,
    #    lambda(*returnargs) -> api return value,
    #    optional: number of return args (default 1),
    # )
    _API_METHODS_GET = {
        "getCallSign": _d,
        "getCurrentWarpSpeed": _d,
        "getDocked": (lambda _: 'getDockedWith()', bool),
        "getDockingState": (_dg, int),
        "getHeading": _d,
        "getVelocity": (_dg, lambda vx, vy: sqrt(vx**2 + vy**2)*60/1000, 2), # returns vx,vy in m/sec but we want units (=1000m) / min
        "getEnergy": (_dg, int),
        "hasWarpDrive": _d,
        "hasJumpDrive": _d,
        "getCombatManeuverCharge": _d,
    }
    _API_METHODS_SET = {
        "setImpulse": (lambda _, imp: "commandImpulse(%.2f)" % imp, _dr), # float from -1 to 1
        "setHeading": (lambda _, hdg: "commandTargetRotation(%i)" % ((hdg-90)%360), _dr), # int between 0 and 360
        "setWarp": (lambda _, wrp: "commandWarp(%i)" % wrp, _dr), # int from 0 to 4
        "setJump": (lambda _, jun: "commandJump(%i)" % (jun*1000), _dr), # float: units to jump
        "setCombatManeuverBoost": (lambda _, bst: "commandCombatManeuverBoost(%.2f)" % bst, _dr), # float from 0 to 1
        "setCombatManeuverStrafe": (lambda _, cms: "commandCombatManeuverStrafe(%.2f)" % cms, _dr), # float from -1 to 1 (left is negative and right is positive)
    }

    def __init__(self, autosync=True):
        """
            Interface for communication with EmptyEpsilon Lua API via host adapter.
            
            Args:
                bundle: Only send commands when calling communicate() method
        """
        self.autosync = autosync
        for fn in set(self._API_METHODS_GET.keys()) | set(self._API_METHODS_SET.keys()):
            def _mklambda(fn):
                # this is needed due to scoping issues with the fn var
                if autosync:
                    return lambda *args: self._apicall_autosync(fn, *args)
                else:
                    return lambda *args: self._apicall_cache(fn, *args)
            setattr(self, fn, _mklambda(fn))
        if autosync:
            self.data = {}
        else:
            self.subscriptions = set()
            self.synced_subscriptions = set()
            self.scheduled = []

        self.led_pin = machine.Pin(25, machine.Pin.OUT)
        self.cdc = CDCInterface()
        self.cdc.init(timeout=0)  # zero timeout makes this non-blocking, suitable for os.dupterm()

        # pass builtin_driver=True so that we get the built-in USB-CDC alongside,
        # if it's available.
        usb.device.get().init(self.cdc, builtin_driver=True)

        print("Waiting for USB host to configure the interface...")

        # wait for host enumerate as a CDC device...
        while not self.cdc.is_open():
            time.sleep_ms(100)
        print("CDC port enumerated")

        print("Waiting for host adapter")
        self.wait_host_adapter()

        #print("Connected to ship: " + self.getCallSign())

    def wait_host_adapter(self):
        self.led_pin.low()
        # wait for host adapter
        while not self.cdc.rts:
            time.sleep_ms(100)

        print("Host adapter detected")
        self.led_pin.high()

    def run_cmd(self, call):
        # TODO: general timeout for this function with reset
        if not self.cdc.rts:
            print("Host adapter not ready - waitig...")
            self.wait_host_adapter()
        self.cdc.read(10000) # clear buffer
        self.led_pin.low()
        self.cdc.write(call+"\n")
        #self.cdc.flush()
        buffer = b""
        while True:
            s = self.cdc.read(10000)
            if s:
                buffer += s
            if buffer.strip():
                try:
                    j = json.loads(buffer)
                    self.led_pin.high()
                    return j
                except:
                    pass

    @classmethod
    def _expand_api_tuple(cls, t):
        if len(t) == 2:
            mkcall, mkret = t
            nretvars = 1
            return (mkcall, mkret, nretvars)
        elif len(t) == 3:
            return t
        else:
            raise Exception("Invalid API_METHOD def for '%s'" % fn)

    def _apicall_autosync(self, fn, *args):
        if fn in self._API_METHODS_GET:
            t = self._API_METHODS_GET[fn]
        elif fn in self._API_METHODS_SET:
            t = self._API_METHODS_SET[fn]
        else:
            raise Exception("Called unknown API method: '%s'" % fn)
        mkcall, mkret, nretvars = self._expand_api_tuple(t)
        retvars = ['r%i' % i for i in range(nretvars)]
        call = '%s=%s' % (','.join(retvars), mkcall(fn, *args))
        ret = self.run_cmd(call)
        return mkret(*map(ret.get, retvars))

    def _apicall_cache(self, fn, *args):
        if fn in self._API_METHODS_GET:
            # get data from cache
            assert fn in self.synced_subscriptions, "'%s' called but not synced" % fn
            t = self._API_METHODS_GET[fn]
            _, mkret, nretvars = self._expand_api_tuple(t)
            retvars = ['%s_%i' % (fn, i) for i in range(nretvars)]
            return mkret(*map(self.data.get, retvars))
        elif fn in self._API_METHODS_SET:
            # schedule cmd
            self.scheduled.append((fn, args))
        else:
            raise Exception("Called unknown API SET method: '%s'" % fn)

    def sync(self):
        assert not self.autosync, "autosync=True"
        calls = []
        def _gencall(fn, tc, *args):
            mkcall, _, nretvars = self._expand_api_tuple(tc[fn])
            retvars = ['%s_%i' % (fn, i) for i in range(nretvars)]
            calls.append('%s=%s' % (','.join(retvars), mkcall(fn, *args)))
        for fn, args in self.scheduled:
            _gencall(fn, self._API_METHODS_SET, *args)
        self.scheduled = []
        for fn in self.subscriptions:
            _gencall(fn, self._API_METHODS_GET)
        self.data = self.run_cmd('&'.join(calls))
        self.synced_subscriptions = self.subscriptions.copy()

    def subscribe(self, cmd):
        self.subscriptions.add(cmd)

    def unsubscribe(self, cmd):
        self.subscriptions.remove(cmd)

NOT_DOCKED = 0
DOCKING = 1
DOCKED = 2
