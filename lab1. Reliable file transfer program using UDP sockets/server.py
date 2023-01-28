#SD20-01
#Vagif Khalilov
#Distributed and Network Programming lab 1
import socket
import time
import sys

HOST = 'localhost'
PORT = 12300
BUFFER = 1024
TIMEOUT = 0.5

def save_file(data, filename):
    f = open(f'{filename}', 'wb+')
    f.write(data)
    f.close()

def check_sessions(sessions):
    #firstly we need to remove finished sessions
    for client in list(sessions.keys()):
        last_message = sessions[client]['last_message']
                
        if time.time() - last_message < 1:
            continue
                
        current_file = sessions[client]['file']
        total_size = sessions[client]['total_size']
        filename = sessions[client]['filename']
        if len(current_file) == total_size:
            sessions.pop(client)
            save_file(current_file, filename)
            print(f"The session with client {client} is finished successfully.")

    #remove inactive sessions
    for client in list(sessions.keys()):
        last_message = sessions[client]['last_message']
        if time.time() - last_message >= 3:
            sessions.pop(client)
            print(f"The client {client} is not active for more than 3s. Session terminated. Data deleted")

def server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    sock.settimeout(TIMEOUT)
    sessions = {}
    print("Server started")
    while True:

        #checking
        check_sessions(sessions)

        #try to recive
        try:
            message, address = sock.recvfrom(BUFFER)
            #print(message.decode())
        except:
            continue
        
        message_type = message[:1].decode()
        #handling message
        type = message[:1].decode()
        if  type == 's':

            message = message.decode()
            _, seqno, filename, total_size = message.split(' | ')      
                
            sessions[address[1]] = {
                'seqno': int(seqno) + 1,
                'filename': filename,
                'total_size': int(total_size),
                'last_message': time.time(),
                'file': b''
            }
            answer = f'a | {int(seqno) + 1} | {BUFFER}'
            sock.sendto(answer.encode(), address)

        if type == 'd':
            pos1 = list(message).index(124)
            pos2 = list(message).index(124, pos1 + 1)
            sessions[address[1]]['last_message'] = time.time()
            seqno = int(message[pos1 + 1: pos2])
            data = message[pos2 + 2:]
            if seqno == sessions[address[1]]['seqno']:
                sessions[address[1]]['seqno'] = seqno + 1
                sessions[address[1]]['file'] += data

                answer = f'a | {seqno + 1}'
                sock.sendto(answer.encode(), address)




if __name__ == '__main__':
    if len(sys.argv) == 4:
        PORT = int(sys.argv[1])
    server()