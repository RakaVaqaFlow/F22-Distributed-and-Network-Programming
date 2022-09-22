"""
DNP: Lab 03: using ZeroMQ to organize a distributed system
Name Surname: Vagif Khalilov
Email: v.khalilov@innopolis.university
Group: BS20-SD-01

"""
import zmq
import time
import sys

CLIENT_IN = 5555
CLIENT_OUT = 5556
WORKER_IN = 5557
WORKER_OUT = 5558


def checker(args):
    # we can throw exceptions and use try catch case in the main instead of outputting an error to the console
    if len(args) != 5:
        print("Please, run the server again with arguments <client in> <client out> <worker in> <worker out>\n example: python3 client.py 5555 5556")
        sys.exit(1)
    for i in range(1, 5):
        try:
            if int(args[i]) > 65535 or int(args[i]) < 1:
                print(
                    'Invalid format of the port, integer in the range [1, 65535] is expected')
                sys.exit(1)
        except:
            print(
                'Invalid format of the port, integer in the range [1, 65535] is expected')
            sys.exit(1)
    global CLIENT_IN
    CLIENT_IN = int(args[1])

    global CLIENT_OUT
    CLIENT_OUT = int(args[2])

    global WORKER_IN
    WORKER_IN = int(args[3])

    global WORKER_OUT
    WORKER_OUT = int(args[4])


def server():
    context = zmq.Context()
    # client input - REP
    client_in = context.socket(zmq.REP)
    client_in.bind(f'tcp://127.0.0.1:{CLIENT_IN}')
    # client output - PUB
    client_out = context.socket(zmq.PUB)
    client_out.bind(f'tcp://127.0.0.1:{CLIENT_OUT}')
    # worker input - PUB
    worker_in = context.socket(zmq.PUB)
    worker_in.bind(f'tcp://127.0.0.1:{WORKER_IN}')
    # worker output - SUB
    worker_out = context.socket(zmq.SUB)
    worker_out.bind(f'tcp://127.0.0.1:{WORKER_OUT}')
    worker_out.setsockopt_string(zmq.SUBSCRIBE, '')
    worker_out.RCVTIMEO = 100
    try:
        while True:
            try:
                message = client_in.recv_string()
                # must send back to enable next state
                # client_in.send_string('')
                command = message.split(' ')
                if (len(command) == 2 and command[0] == 'isprime' and command[1].isdigit()) or \
                   (len(command) == 3 and command[0] == 'gcd' and command[1].isdigit() and command[2].isdigit()):
                    worker_in.send_string(message)
                    work_res = worker_out.recv_string()
                    client_out.send_string(work_res)
                client_out.send_string(message)
            except zmq.Again:
                pass
    except KeyboardInterrupt:
        print("Terminating client")
        sys.exit(0)


if __name__ == "__main__":
    checker(sys.argv)
    server()
