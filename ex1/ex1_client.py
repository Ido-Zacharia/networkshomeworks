#!/usr/bin/env python3

import sys
from socket import *

DEFPORT = 1337
DEFHOSTNAME = "localhost"

def is_valid_host(s: str) -> bool:
    return is_ipv4(s) or is_ipv6(s) or is_hostname(s)


def is_ipv4(s: str) -> bool:
    parts = s.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        # No leading zeros unless the number is exactly "0"
        if part != "0" and part.startswith("0"):
            return False
        num = int(part)
        if not (0 <= num <= 255):
            return False
    return True


def is_ipv6(s: str) -> bool:
    parts = s.split(":")
    # IPv6 must have 3–8 parts unless "::" compression is used
    if len(parts) < 3 or len(parts) > 8:
        return False

    empty_parts = 0
    for part in parts:
        if part == "":
            empty_parts += 1
            continue
        if len(part) > 4:
            return False
        for ch in part:
            if not (ch.isdigit() or ch.lower() in "abcdef"):
                return False

    # "::" compression: only one instance allowed
    if empty_parts > 2:
        return False
    if empty_parts == 2 and s.count("::") != 1:
        return False

    return True


def is_hostname(s: str) -> bool:
    # Hostname length rules
    if len(s) == 0 or len(s) > 253:
        return False

    labels = s.split(".")
    for label in labels:
        if len(label) == 0 or len(label) > 63:
            return False
        # Labels must start/end with letter or digit
        if not (label[0].isalnum() and label[-1].isalnum()):
            return False
        # Allowed chars: letters, digits, hyphen
        for ch in label:
            if not (ch.isalnum() or ch == "-"):
                return False

    return True


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
    if not is_valid_host(host): # Either IP or a name
        sys.exit(-1)
    return host, port


def recv_or_die(sock):
    """Receive once; exit if server closed."""
    data = sock.recv(1024)
    if not data:
        print("server closed connection")
        sys.exit(1)
    return data.decode("utf-8")


def main():
    host_name, port_num = parse_args()

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host_name, port_num))

    # read welcome banner
    banner = recv_or_die(sock)
    print(banner, end="")

    # LOGIN LOOP
    logged_in = False
    while not logged_in:
        user_name = input("")
        password = input("")

        msg = f"{user_name}\n{password}\n"
        sock.sendall(msg.encode("utf-8"))

        try:
            resp_raw = sock.recv(1024)
        except ConnectionError:
            print("server closed connection")
            sock.close()
            sys.exit(1)

        if not resp_raw:
            print("server closed connection")
            sock.close()
            sys.exit(1)

        resp = resp_raw.decode("utf-8")
        print(resp, end="")

        if resp.startswith("Hi "):
            # successful login
            logged_in = True
        elif resp.startswith("Failed to login"):
            # wrong password / username – retry
            continue
        elif resp.startswith("error: invalid input"):
            # server decided the login format is invalid and will close
            sock.close()
            sys.exit(1)
        else:
            # unexpected response – safest is to exit
            sock.close()
            sys.exit(1)

    # COMMAND LOOP
    while True:
        try:
            req = input()
        except EOFError:
            return
        req = req.strip()
        if not req:
            continue

        # server expects newline-terminated commands
        line = req + "\n"
        try:
            sock.sendall(line.encode("utf-8"))
        except ConnectionError:
            print("server closed connection")
            break

        if req == "quit":
            # According to spec, server closes the connection after 'quit'
            break

        try:
            data = sock.recv(1024)
        except ConnectionError:
            print("server closed connection")
            break

        if not data:
            print("server closed connection")
            break

        answer = data.decode("utf-8")
        print(answer, end="")

    sock.close()


if __name__ == "__main__":
    main()
