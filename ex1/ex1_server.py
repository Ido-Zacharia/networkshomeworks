import sys
import math
import select
from socket import *

BUFFER_SIZE = 2 ** 15
DEFPORT = 1337
ERR_MSSG = b"error: invalid input, log out!\n"
ERR_MSSG_CAESAR = b"error: invalid input\n"

# ---------- helpers ----------

def load_users(path):
    users = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # file is tab-delimited according to the spec
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            username, password = parts
            users[username] = password
    return users


def parentheses_checker(plaintext: str):
    """
    Returns:
      True / False if only '(' and ')' are present and we can compute balance
      ERR_MSSG     if any other character appears
    """
    cnt = 0
    def_val = True
    for ch in plaintext:
        if ch == '(':
            cnt += 1
        elif ch == ')':
            cnt -= 1
        else:
            # invalid character
            return ERR_MSSG
        if cnt < 0:
            def_val = False
    return cnt == 0 and def_val


def legit_ch(ch):
    o = ord(ch)
    if 65 <= o <= 90:
        return True  # A-Z
    if 97 <= o <= 122:
        return True  # a-z
    if ch == " ":
        return True
    return False


def caesar_cipher(plaintext: str, shift: int):
    shift = shift % 26
    res = []
    base = ord('a')

    for ch in plaintext:
        if not legit_ch(ch):
            return ERR_MSSG
        if ch == " ":
            res.append(" ")
        else:
            idx = ((ord(ch.lower()) - base) + shift) % 26
            res.append(chr(base + idx))
    return "".join(res)


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


# ---------- request handler ----------

def handle_line(curr_client, sock, line, users, clients):
    """
    Handle a single logical line from a client.
    If the client is closed inside this function, it must not be used afterwards.
    """
    req_action = curr_client["required_action"]

    # LOGIN PHASE – USERNAME
    if req_action == "username":
        if not line.startswith("User: "):
            sock.sendall(ERR_MSSG)
            close_client(sock, clients)
            return

        username = line[len("User: "):].strip()
        if not username:
            sock.sendall(ERR_MSSG)
            close_client(sock, clients)
            return

        curr_client["username"] = username
        curr_client["required_action"] = "password"
        return

    # LOGIN PHASE – PASSWORD
    if req_action == "password":
        if not line.startswith("Password: "):
            sock.sendall(ERR_MSSG)
            close_client(sock, clients)
            return

        password = line[len("Password: "):].strip()
        uname = curr_client["username"]

        if uname in users and users[uname] == password:
            curr_client["required_action"] = "action"
            msg = f"Hi {uname}, good to see you.\n"
            sock.sendall(msg.encode("utf-8"))
        else:
            # credentials are wrong – allow another try
            sock.sendall(b"Failed to login\n")
            curr_client["required_action"] = "username"
            curr_client["username"] = None
        return

    # COMMAND PHASE (req_action == "action")

    # 1. parentheses
    if line.startswith("parentheses:"):
        expr = line[len("parentheses:"):].strip()
        balanced = parentheses_checker(expr)

        if balanced is ERR_MSSG:
            sock.sendall(ERR_MSSG)
            close_client(sock, clients)
            return

        answer = "yes" if balanced else "no"
        msg = f"the parentheses are balanced: {answer}\n"
        sock.sendall(msg.encode("utf-8"))
        return

    # 2. lcm
    if line.startswith("lcm:"):
        rest = line[len("lcm:"):].strip()
        parts = rest.split()
        if len(parts) != 2:
            sock.sendall(ERR_MSSG)
            close_client(sock, clients)
            return
        try:
            x = int(parts[0])
            y = int(parts[1])
        except ValueError:
            sock.sendall(ERR_MSSG)
            close_client(sock, clients)
            return

        res = lcm_(x, y)
        msg = f"the lcm is: {res}\n"
        sock.sendall(msg.encode("utf-8"))
        return

    # 3. caesar
    if line.startswith("caesar:"):
        rest = line[len("caesar:"):].strip()
        try:
            text_part, shift_str = rest.rsplit(" ", 1)
            shift = int(shift_str)

        except ValueError:
            sock.sendall(ERR_MSSG)
            close_client(sock, clients)
            return

        cipher = caesar_cipher(text_part, shift)
        if cipher is ERR_MSSG:
            sock.sendall(ERR_MSSG_CAESAR)
            return

        msg = f"the ciphertext is: {cipher}\n"
        sock.sendall(msg.encode("utf-8"))
        return

    # 4. quit
    if line == "quit":
        close_client(sock, clients)
        return

    # anything else
    sock.sendall(ERR_MSSG)
    close_client(sock, clients)

# ---------- main ----------

def main():
    # args: users_file [port]
    if len(sys.argv) < 2:
        print("not enough args")
        sys.exit(1)
    if len(sys.argv) > 3:
        print("too many args")
        sys.exit(1)

    users_file = sys.argv[1]

    if len(sys.argv) == 2:
        port_num = DEFPORT
    else:
        try:
            port_num = int(sys.argv[2])
        except ValueError:
            print("port must be a number")
            sys.exit(1)

    users = load_users(users_file)

    listening_socket = socket(AF_INET, SOCK_STREAM)
    listening_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listening_socket.bind(("", port_num))
    listening_socket.listen(100)

    clients = {}

    while True:
        read_list = [listening_socket] + list(clients.keys())
        ready_to_read, _, _ = select.select(read_list, [], [])

        for sock in ready_to_read:
            # New connection
            if sock is listening_socket:
                client_sock, addr = listening_socket.accept()
                clients[client_sock] = {
                    "username": None,
                    "required_action": "username",
                    "addr": addr,
                    "buffer": "",
                }
                # Greeting
                client_sock.sendall(b"Welcome! Please log in.\n")
                continue

            # Existing client
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

            # process all full lines from buffer
            while "\n" in curr_client["buffer"]:
                line, curr_client["buffer"] = curr_client["buffer"].split("\n", 1)
                line = line.rstrip("\r")
                if line == "":
                    continue

                handle_line(curr_client, sock, line, users, clients)

                # If the client was closed inside handle_line, stop.
                if sock not in clients:
                    break


if __name__ == "__main__":
    main()
