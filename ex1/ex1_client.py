#!/usr/bin/env python3

import sys
from socket import *

DEFPORT = 1337
DEFHOSTNAME = "localhost"
ERR_MSSG = "error: invalid input\n"


def parse_args():
    argc = len(sys.argv)
    if argc == 1:
        host = DEFHOSTNAME
        port = DEFPORT
    elif argc == 2:
        host = sys.argv[1]
        port = DEFPORT
    elif argc == 3:
        host = sys.argv[1]
        if not sys.argv[2].isdigit():
            print("port must be a number")
            sys.exit(1)
        port = int(sys.argv[2])
    else:
        print("too many args")
        sys.exit(1)
    return host, port


def main():
    host_name, port_num = parse_args()

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host_name, port_num))

    # read welcome banner
    banner = sock.recv(1024).decode("utf-8")
    print(banner, end="")

    # LOGIN LOOP
    logged_in = False
    while not logged_in:
        user_name = input("")
        password = input("")

        msg = f"{user_name}\n{password}\n"
        sock.sendall(msg.encode())

        resp = sock.recv(1024).decode("utf-8")
        print(resp, end="")
        logged_in = True

    # COMMAND LOOP
    while True:
        req = input("").strip()
        if not req:
            continue

        # server expects a line ending in '\n'
        line = req + "\n"
        sock.sendall(line.encode())

        if req == "quit":
            break

        data = sock.recv(1024)
        if not data:
            print("Server closed the connection.")
            break

        answer = data.decode("utf-8")
        print(answer, end="")

            

    sock.close()


if __name__ == "__main__":
    main()
