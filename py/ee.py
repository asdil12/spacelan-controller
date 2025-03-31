import machine
import json
import time

import usb.device
from usb.device.cdc import CDCInterface

cdc = CDCInterface()
cdc.init(timeout=0)  # zero timeout makes this non-blocking, suitable for os.dupterm()

def init():
    # called from main.py
    # pass builtin_driver=True so that we get the built-in USB-CDC alongside,
    # if it's available.
    usb.device.get().init(cdc, builtin_driver=True)

    print("Waiting for USB host to configure the interface...")

    # wait for host enumerate as a CDC device...
    while not cdc.is_open():
        time.sleep_ms(100)
    print("CDC port enumerated")

    print("Waiting for host adapter")
    wait_host_adapter()

    print("Connected to ship: " + getCallSign())

led_pin = machine.Pin(25, machine.Pin.OUT)

def wait_host_adapter():
    led_pin.low()
    # wait for host adapter
    while not cdc.rts:
        time.sleep_ms(100)

    print("Host adapter detected")
    led_pin.high()

def run_cmd(cmd):
    if not cdc.rts:
        print("Host adapter not ready - waitig...")
        wait_host_adapter()
    cdc.read(10000) # clear buffer
    cdc.write(cmd+"\n")
    cdc.flush()
    buffer = b""
    while True:
        s = cdc.read(10000)
        if s:
            buffer += s
        if buffer.strip():
            try:
                j = json.loads(buffer)
                return j
            except:
                pass

def getCallSign():
    return run_cmd('cs=getCallSign()')['cs']

def getWarp():
    return run_cmd('cws=getCurrentWarpSpeed()')['cws']

def getDocked():
    return bool(run_cmd("ws=getDockedWith()"))

NOT_DOCKED = 0
DOCKING = 1
DOCKED = 2

def getDockingState():
    return int(run_cmd("ds=getDockingState()")['ds'])

def getHeading():
    return int(run_cmd("h=getHeading()")['h'])

def setHeading(heading):
    run_cmd("f=commandTargetRotation(%i)" % ((heading-90)%360))

def getVelocity():
    from math import sqrt
    j = run_cmd("x,y=getVelocity()")
    x, y = j['x'], j['y']
    v = sqrt(x*x + y*y)
    # v is velocity in meters / second but we want units (=1000m) / minute 
    return (v * 60) / 1000

def getEnergy():
    return int(run_cmd("e=getEnergy()")['e'])

def setImpulse(impulse):
    # float from -1 to 1
    run_cmd("f=commandImpulse(%.2f)" % impulse)

def setWarp(warp):
    # int from 0 to 4
    run_cmd("f=commandWarp(%i)" % warp)

def hasWarpDrive():
    return run_cmd("wd=hasWarpDrive()")['wd']

def hasJumpDrive():
    return run_cmd("jd=hasJumpDrive()")['jd']

def setJump(units):
    # float
    return run_cmd("f=commandJump(%i)" % (units*1000))

# TODO: commandCombatManeuverBoost
