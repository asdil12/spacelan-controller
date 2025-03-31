#!/usr/bin/python3

import serial
from glob import glob
import json
import requests
import threading
from time import sleep

def adapter(sd):
    try:
        print(f"Using {sd}")
        s = serial.Serial(sd)
        buffer = b""
        while True:
            buffer += s.read()
            if buffer.endswith(b"\n"):
                cmd = buffer.strip().decode()
                print(f"CMD: {cmd}", end='')
                r = requests.get(f'http://127.0.0.1:8080/get.lua?{cmd}')
                res = json.dumps(r.json())
                print(f" -> {res}")
                s.write(res.encode())
                s.flush()
                buffer = b""
    except serial.serialutil.SerialException as e:
        print(f"Device {sd} closed:\n  {e}")

print("Waiting for devices")
threads = {}

while True:
    for sd in list(threads.keys()):
        thread = threads[sd]
        if not thread.is_alive():
            print(f"Cleaning up dead {thread}")
            del threads[sd]
    serial_devices = glob("/dev/serial/by-id/usb-MicroPython*-if02")
    for sd in serial_devices:
        if not threads.get(sd):
            thread = threading.Thread(target=adapter, args=[sd], daemon=True, name=f"adapter:{sd}")
            print(f"Spawning {thread} for new device")
            threads[sd] = thread
            thread.start()
    sleep(1)
