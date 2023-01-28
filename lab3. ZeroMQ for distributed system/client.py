"""
DNP: Lab 03: using ZeroMQ to organize a distributed system
Name Surname: Vagif Khalilov
Email: v.khalilov@innopolis.university
Group: BS20-SD-01

"""
from unittest import result
import zmq
import time
import sys

CLIENT_IN = 5555
CLIENT_OUT = 5556


def checker(args):
    # we can throw exceptions and use try catch case in the main instead of outputting an error to the console
    if len(args) != 3:
        print("Please, run the client again with arguments <client in> <client out>\n example: python3 client.py 5555 5556")
        sys.exit(1)
    for i in range(1, 3):
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


def client():
    context = zmq.Context()
    # client input - REQ
    client_in = context.socket(zmq.REQ)
    client_in.connect(f'tcp://127.0.0.1:{CLIENT_IN}')
    # client output - SUB
    client_out = context.socket(zmq.SUB)
    client_out.connect(f'tcp://127.0.0.1:{CLIENT_OUT}')
    client_out.setsockopt_string(zmq.SUBSCRIBE, '')
    client_out.RCVTIMEO = 100

    try:
        while True:
            message = input('> ')
            if len(message) != 0:
                client_in.send_string(message)
                client_in.recv()
            try:
                result = client_out.recv_string()
                print(result)
            except zmq.Again:
                pass
    except KeyboardInterrupt:
        print("Terminating client")
        sys.exit(0)


if __name__ == "__main__":
    checker(sys.argv)
    client()
