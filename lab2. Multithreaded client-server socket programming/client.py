"""
Name Surname: Vagif Khalilov
Group: SD20-01
DNP Lab 2

"""
import socket
import sys

numbers = [15492781, 15492787, 15492803,
 15492811, 15492810, 15492833,
 15492859, 15502547, 15520301,
 15527509, 15522343, 1550784]

HOST = '127.0.0.1'
PORT = 5555

def checker():
    #we can throw exceptions and use try catch case in the main instead of outputting an error to the console
    num = HOST.split('.')
    if len(num) != 4:
        print('Invalid format of the server ip address')
        sys.exit(1)
    for i in num:
        if int(i)>127 or int(i)<0:
            print('Invalid format of the server ip address')
            sys.exit(1)
    if PORT>65535 or PORT<1:
        print('Invalid format of the server port')
        sys.exit(1)

def client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to ('{HOST}', {PORT})")
        for i in numbers:
            message = f"{i}"
            s.sendall(message.encode())
            data = s.recv(1024)
            data = data.decode()
            if len(data) !=0:
                if data == 'True':
                    print(f"{i} is prime")
                else:
                    print(f"{i} is not prime")
        print("Completed")

                

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please, run the client again with arguments <ip-addr>:<port> of the server\n example: python3 client.py 127.0.0.1:5555")
        sys.exit(1)
    HOST = sys.argv[1].split(':')[0]
    PORT = int(sys.argv[1].split(':')[1])
    checker()
    client()