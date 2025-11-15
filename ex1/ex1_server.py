#!/usr/bin/env python3

from socket import *
import sys
import select
import math


BUFFER_SIZE = 2 ** 12
ERR_MSSG = "error: invalid input\n"

DEFPORT = 1337


# --------- helpers ----------

def load_users(path):
    users = {}
    with open(path, "r") as curr_file:
        for line in curr_file:
            line = line.strip()
            if not line:
                continue
            partition = line.split("\t")
            if len(partition) != 2:
                continue
            username, password = partition
            users[username] = password
    return users


def parentheses_checker(plaintext: str):
    defval = True
    cnt = 0
    for char in plaintext:
        if char == '(':
            cnt += 1
        elif char == ')':
            cnt -= 1
        else:
            return ERR_MSSG
        if cnt < 0:
            defval = False
    return (cnt == 0) and defval


def legit_ch(ch):
    order = ord(ch)
    if (65 <= order <= 90) or (97 <= order <= 122) or ch == " ":
        return True
    return False


def caser(plaintext: str, shft: int):
    shift = shft % 26
    res = []
    base = ord('a')

    for ch in plaintext:
        if not legit_ch(ch):
            return ERR_MSSG
        if ch == ' ':
            res.append(' ')
        else:
            idx = ((ord(ch.lower()) - base) + shift) % 26
            res.append(chr(base + idx))
    return ''.join(res)


def lcm_(x: int, y: int):
    if x == 0 or y == 0:
        return 0
    return abs(x * y) // math.gcd(x, y)


def close_client(sock, clients):
    clients.pop(sock, None)
    try:
        sock.close()
    except OSError:
        pass


# --------- request handler ----------

def handler(curr_client, sock, line, users, clients):
    req_action = curr_client["required_action"]

    # LOGIN: USERNAME
    if req_action == "username":
        if not line.startswith("User: "):
            close_client(sock, clients)
            return

        username = line[len("User: "):].strip()
        if not username:
            close_client(sock, clients)
            return

        curr_client["username"] = username
        curr_client["required_action"] = "password"
        return

    # LOGIN: PASSWORD
    if req_action == "password":
        if not line.startswith("Password: "):
            sock.sendall(ERR_MSSG.encode())
            close_client(sock, clients)
            return

        password = line[len("Password: "):].strip()
        uname = curr_client["username"]

        if uname in users and users[uname] == password:
            curr_client["required_action"] = "action"
            msg = f"Hi {uname}, good to see you.\n"
            sock.sendall(msg.encode())
        else:
            sock.sendall(b"Failed to login.\nUser: ")
            curr_client["required_action"] = "username"
            curr_client["username"] = None
        return

    # COMMAND PHASE (req_action == "action")
    if line.startswith("parentheses:"):
        expression = line[len("parentheses:"):].strip()

        balanced = parentheses_checker(expression)
        if balanced == ERR_MSSG:
            sock.sendall(ERR_MSSG.encode())
            return

        answer = "yes" if balanced else "no"
        msg = f"the parentheses are balanced: {answer}\n"
        sock.sendall(msg.encode())
        return

    if line.startswith("lcm:"):
        rest = line[len("lcm:"):].strip()
        parts = rest.split()
        if len(parts) != 2:
            sock.sendall(ERR_MSSG.encode())
            return
        try:
            x = int(parts[0])
            y = int(parts[1])
        except ValueError:
            sock.sendall(ERR_MSSG.encode())
            return

        retval = lcm_(x, y)
        msg = f"the lcm is: {retval}\n"
        sock.sendall(msg.encode())
        return

    if line.startswith("caesar:"):
        rest = line[len("caesar:"):].strip()

        try:
            text_part, shift_str = rest.rsplit(" ", 1)
            shift = int(shift_str)

        except ValueError:
            sock.sendall(ERR_MSSG.encode())
            return

        cipher = caser(text_part, shift)
        if cipher == ERR_MSSG:
            sock.sendall(ERR_MSSG.encode())
            return

        msg = f"the ciphertext is: {cipher}\n"
        sock.sendall(msg.encode())
        return

    if line == "quit":
        close_client(sock, clients)
        return

    # anything else
    sock.sendall(ERR_MSSG.encode())


# --------- main loop ----------

def main():
    if len(sys.argv) < 2:
        print("not enough args")
        sys.exit(1)
    elif len(sys.argv) > 3:
        print("too many args")
        sys.exit(1)

    users_file = sys.argv[1]
    port_num = DEFPORT if len(sys.argv) != 3 else int(sys.argv[2])

    users = load_users(users_file)

    listeningSocket = socket(AF_INET, SOCK_STREAM)
    listeningSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listeningSocket.bind(("", port_num))
    listeningSocket.listen(100)

    clients = {}

    while True:
        read_list = [listeningSocket] + list(clients.keys())
        ready_to, _, _ = select.select(read_list, [], [])

        for sock in ready_to:
            # new connection
            if sock is listeningSocket:
                client_sock, addr = listeningSocket.accept()
                clients[client_sock] = {
                    "username": None,
                    "required_action": "username",
                    "addr": addr,
                    "buffer": "",
                }
                # you can change text to exactly match the spec if needed
                client_sock.sendall(b"Welcome! Please log in.\n")
                continue  # DO NOT fall through

            # existing client
            try:
                data = sock.recv(BUFFER_SIZE)
            except ConnectionError:
                data = b""

            if not data:
                close_client(sock, clients)
                continue

            curr_client = clients.get(sock)
            if curr_client is None:
                close_client(sock, clients)
                continue

            curr_client["buffer"] += data.decode("utf-8")

            while "\n" in curr_client["buffer"]:
                line, curr_client["buffer"] = curr_client["buffer"].split("\n", 1)
                line = line.rstrip("\r")
                if line == "":
                    continue
                handler(curr_client, sock, line, users, clients)


if __name__ == "__main__":
    main()
