"""
Name Surname: Vagif Khalilov
Group: SD20-01
DNP Lab 2

"""
import socket
from threading import Thread
from multiprocessing import Queue
import sys


MAX_CONNECTIONS = 10
WORKERS_NUMBER = 5
HOST = '127.0.0.1'
PORT = 5555
clients_queue = Queue(MAX_CONNECTIONS)

#we can throw exceptions and use try catch case in the main instead of outputting an error to the console
#check arguments
def checker():
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

#function from lab description
def is_prime(n):
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    for divisor in range(3, n, 2):
        if n % divisor == 0:
            return False
    return True

def handle_connection(connection, address):
    with connection:
        while True:
            data = connection.recv(1024)
            data = data.decode()
            answer = ''
            if len(data) !=0:
                answer = f"{is_prime(int(data))}"
            if not data:
                break
            connection.sendall(answer.encode())
        

def worker():
    while True:
        if not clients_queue.empty():
            connection, address = clients_queue.get()
            handle_connection(connection, address)
            print(f"('{HOST}', {PORT}) disconnected from worker")
        
    
def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.listen(MAX_CONNECTIONS)

        for i in range(WORKERS_NUMBER):
            t = Thread(target=worker, args=(), daemon=True)
            t.start()
        while True:     
            try:
                connection, address = sock.accept()
                print(f"('{HOST}', {PORT}) connected")
                clients_queue.put((connection, address))
            except KeyboardInterrupt:
                print("Shutting down\nDone")
                sys.exit(1)
            
        

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please, run the server again with argument <port>\n example: python3 server.py 5555")
        sys.exit(1)
    PORT = int(sys.argv[1])
    checker()
    server()
    