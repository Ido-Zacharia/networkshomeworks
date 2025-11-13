import sys
from socket import *


DEFPORT = 1337
DEFHOSTNAME = 'localhost'




def main():
    host_name = DEFHOSTNAME
    if len(sys.argv) == 2 and sys.argv[1].is_digit(): #host name is missing
        print(f"missing host name")
        sys.exit(1)

    elif len(sys.argv) == 2 or len(sys.argv) == 3:
        host_name = sys.argv[1]

    elif len(sys.argv) > 3: #too many params
        print(f"too many args")
        sys.exit(1)

    actions = ["parentheses", "lcm", "caesar", "quit"]

    port_num = DEFPORT if len(sys.argv) != 3 else int(sys.argv[2])

    curr_action = "login"

    listeningSocket = socket(AF_INET, SOCK_STREAM) #AF_INET <-> IPv4 , SOCK_STREAM <-> TCP

    listeningSocket.connect((host_name, port_num))

    while curr_action != "quit":
        if curr_action == "login":
            user_name = input("Enter your username: ")
            password = input("Enter your password: ")
            msg = f"User: {user_name}\n Password: {password}\n"
            listeningSocket.sendall(msg.encode())
            data = listeningSocket.recv(1024)
            if data.decode() == "Hi {user_name}, good to see you.\n":
                curr_action = "send request"
                continue
        curr_action = input("Enter your request:")
        if curr_action in actions:
            match curr_action:
                case "parentheses":
                    expr = input("Enter your expression:")
                    msg = f"parentheses: {expr}\n"
                case "lcm":
                    nums = input("Enter your numbers (space separated):")
                    msg = f"lcm: {nums}\n"
                case "caesar":
                    shift = input("Enter shift value:")
                    text = input("Enter text:")
                    msg = f"caesar: {text} {shift}\n"
                case "quit":
                    msg = "quit\n"
            listeningSocket.sendall(msg.encode())
            if curr_action == "quit":
                break
            data = listeningSocket.recv(1024)
            
            print("Received from server:", data.decode())
        else:
            print("Invalid action. Please try again.")
    
    listeningSocket.close()