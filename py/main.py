from pye import pye

import os
import time
import machine

import ee

eei = ee.EmptyEpsilonInterface(autosync=False)

eei.subscribe('getHeading')
eei.subscribe('getEnergy')
eei.subscribe('getDocked')
eei.subscribe('getCurrentWarpSpeed')
eei.subscribe('getVelocity')
eei.subscribe('getCombatManeuverCharge')

# setting up pins
a0 = machine.ADC(26)
a1 = machine.ADC(27)

a0vn = 0
a1vn = 0

def mainloop():
    global a0vn, a1vn
    while True:
        eei.sync()
        a0v = a0.read_u16()
        a1v = a1.read_u16()
        a0vn = int((a0vn * 19 + a0v) / 20)
        a1vn = int((a1vn * 19 + a1v) / 20)
        print(str(a0vn) + " " + str(a1vn) + " " + repr(eei.getVelocity()))
        eei.setHeading(eei.getHeading() + 1)

#mainloop()
