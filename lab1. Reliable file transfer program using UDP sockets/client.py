#SD20-01
#Vagif Khalilov
#Distributed and Network Programming lab 1
import socket
import os
import sys

SERVER_HOST = 'localhost'
SERVER_PORT = 12300
PATH = "test.pdf"
FILENAME = "file_on_server.pdf"
TIMEOUT = 0.5
BUFFER = 1024

def client():
    
    server = (SERVER_HOST, SERVER_PORT)
    server_buffer = 0
    #data description
    file = open(PATH, 'rb')
    data = file.read()
    total_size = os.path.getsize(PATH)
    filename = FILENAME
    seqno = 0

    #socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    sock.settimeout(TIMEOUT)

    #start working with server

    #sending start message
    cnt = 0
    while cnt < 5:
        cnt += 1
        start_message = f"s | {seqno} | {filename} | {total_size}"
        sock.sendto(start_message.encode(), server)
        try:
            # receive response from server
            response, address = sock.recvfrom(BUFFER)
            response = response.decode().split(' | ')
            if len(response)!=3 and response[0] != 'a':
                print("Incorrect message from server.")
                continue
            server_buffer = int(response[2])
            seqno = int(response[1])
            break
        except:
            continue
    if cnt == 5:
        print("Server is not available.")
        return
    
    #sending data
    seqno += 1
    cnt = 0
    i = 0
    while i < len(data) and cnt < 5:
        cnt += 1
        message = f"d | {seqno} | ".encode()   
        
        message_size = len(message)
        bytes_left = len(data[i:])
        segment_size = min(server_buffer - message_size, bytes_left)
        
        data_segment = data[i: i + segment_size]
        message += data_segment

        sock.sendto(message, server)
        try:

            response, address = sock.recvfrom(BUFFER)
            response = response.decode().split(' | ')

            if len(response)!=2 and response[0] != 'a':
                print("Incorrect message from server.")
                continue

            i += segment_size

            seqno = int(response[1]) + 1
            cnt = 0
        except:
            continue

    if cnt == 5:
        print("Server is not available.")
        return
    print("File was successfully sent!")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        SERVER_HOST = sys.argv[1].split(':')[0]
        SERVER_PORT = int(sys.argv[1].split(':')[1])
        PATH = sys.argv[2]
        FILENAME = sys.argv[3]
    
    client()