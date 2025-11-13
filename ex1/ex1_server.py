from socket import *
import sys
import select
import math


BUFFER_SIZE = 2 ** 12
ERR_MSSG = "error: invalid input\n"

DEFPORT = 1337
BACKLOG_DEF = 10
#________supported commands__________

def load_users(path):
    """

    """
    users = {}
    with open(path,"r") as curr_file:
        for line in curr_file:
            line = line.strip()
            if not line:
                continue
            partition = line.split("\t")
            if len(partition) != 2:
                continue
            username , password = partition
            users[username] = password
    BACKLOG_DEF += len(users)
    return users

def parentheses_checker(plaintext : str) -> bool:
    if len(plaintext) % 2 != 0:
        return False
    cnt = 0
    for char in plaintext:
        if char == '(':
            cnt += 1
        elif char == ')':
            cnt -= 1
        else:
            return ERR_MSSG
        if cnt < 0:
            return False
    return (cnt == 0)

def legit_ch(ch):
    """"""
    order = ord(ch) 
    if (order >= 65 and order <= 90) or (order >= 97 and order <= 122) or ch == " ":
        return True
    return False

def caser(plaintext : str , shft : int): 
    shift = shift % 26
    res = [] 
    base = ord('a')

    for ch in plaintext:
        if not legit_ch(ch):
            return ERR_MSSG
        if ch == ' ':
            res.append(' ')
        else:
            idx = ((ord(ch.lower()) - base) + shift) % 26
            res.append(chr(base+idx))
    return ''.join(res)


def lcm_(x : int , y : int):
    if x == 0 or y == 0:
        return 0
    return abs(x*y) // math.gcd(x , y)

def quit_server(sock):
    pass


def main():
     
    if len(sys.argv) < 2: #not enough params
        print(f"not enough args")
        sys.exit(1)

    elif len(sys.argv) > 3: #too many params
        print(f"too many args")
        sys.exit(1)

    users_file = sys.argv[1]
    port_num = DEFPORT if len(sys.argv) != 3 else int(sys.argv[2])

    users = load_users(users_file)

    num_users = len(users) + BACKLOG_DEF

    listeningSocket = socket(AF_INET, SOCK_STREAM) #AF_INET <-> IPv4 , SOCK_STREAM <-> TCP

    listeningSocket.bind(("", port_num)) #port number is 1337


    listeningSocket.listen(num_users)

    clients = {} # {sock1: {...},sock2 : {...},sock3 : {...}}

    while True:
        read_list = [listeningSocket] + list(clients.keys) # [a] + [b] -> [a,b]
        ready_to , _ , _ = select.select(read_list,[] , [])

        for sock in ready_to:
            if sock in listeningSocket:

                client_sock , addr = listeningSocket.accept()

                clients[client_sock] = {
                                        "username":None,
                                        "required_action" :"username",
                                        "addr" : addr,
                                        "buffer" : b""                                                 
                                        }
                #finished 
                client_sock.sendall(b"Welcome! please log in.\n")

            else:
                try:
                    data = sock.recv(BUFFER_SIZE)

                except ConnectionError:
                    data = b""
                
            curr_client = clients[sock]
            curr_client['buffer'] += data.decode('utf-8') # decoding data into buffer
             
            while '\n' in curr_client['buffer']:
                line , curr_client['buffer'] = curr_client['buffer'].split( "\n" , 1 )
                line = line.rstrip('\r') # removable
                handler(curr_client, sock, line , users , clients)


def close_client(sock, clients):
    clients.pop(sock)
    sock.close()


def handler(curr_client, sock, line , users , clients):
    req_action = curr_client["required_action"]
    
    if req_action == "username":

        if not line.startswith("User: "):
            close_client(sock, clients)
            return
        
        username = line.split(" ")[1]
        curr_client["username"] = username
        curr_client["required_action"] = "password"
    
    elif req_action == "password":
        if not line.startswith("Password: "):
            close_client(sock, clients)
            return

        milat_maavar = line.split(' ')[1]
        
        if curr_client["username"] in users and users[username] == milat_maavar:
            curr_client["username"] = username
            curr_client["required_action"] = "action request"
            msg = f"Hi {username}, good to see you.\n"
            sock.sendall(msg.encode())
        
        else:
            sock.sendall(b"Failed to login.")
            curr_client["required_action"] = "username"
            curr_client["username"] = None

    else:
        if line.statswith("parentheses:"):
            expression = line.split(" ")[1]

            balanced = parentheses_checker(expression)
            if balanced == ERR_MSSG:
                msg = ERR_MSSG
                sock.sendall(msg.encode())
                close_client(sock, clients)
                return
            answer = "yes" if balanced else "no"
            msg = f"the parentheses are balanced: {answer}\n"
            sock.sendall(msg.encode)
        
        elif line.startswith("lcm:"):

            expressions = line.split(" ")[1:]
            if len(expression) != 2:
                close_client(sock, clients)
                return
            try:
                x = int(expression[0])
                y = int(expression[1])

            except ValueError:
                msg = ERR_MSSG
                sock.sendall(msg.encode())
                close_client(sock, clients)
                return

            retval = lcm_(x,y)
            msg = f"the lcm is: {retval}\n"
            sock.sendall(msg.encode())
        
        elif line.startswith("caesar:"):
            rest = line[len("caesar:"):].strip()

            try:
                text_part, shift_str = rest.rsplit(" ",1)
                shift = int(shift_str)
            
            except ValueError:
                msg = ERR_MSSG
                sock.sendall(msg.encode())
                close_client(sock, clients)
                return
            
            cipher = caser(text_part , shift) 
            msg = f"the ciphertext is: {cipher}\n"
            sock.sendall(msg.encode)

        elif line.startswith("quit"):
            sock.sendall("quit")
            close_client(sock, clients)
        else:
            msg = "error: invalid input\n"
            sock.sendall(msg.encode())
            close_client(sock, clients)
            
