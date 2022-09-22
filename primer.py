"""
DNP: Lab 03: using ZeroMQ to organize a distributed system
Name Surname: Vagif Khalilov
Email: v.khalilov@innopolis.university
Group: BS20-SD-01

"""
import zmq
import time
import sys

WORKER_IN = 5557
WORKER_OUT = 5558


def checker(args):
    # we can throw exceptions and use try catch case in the main instead of outputting an error to the console
    if len(args) != 3:
        print("Please, run the primer again with arguments <worker in> <worker out>\n example: python3 client.py 5555 5556")
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

    global WORKER_IN
    WORKER_IN = int(args[1])

    global WORKER_OUT
    WORKER_OUT = int(args[2])


def my_isprime(n):
    if n == 1:
        return False
    for i in range(2, int(n)):
        if n % i == 0:
            return False

    return True


def primer():
    context = zmq.Context()
    # worker input - SUB
    worker_in = context.socket(zmq.SUB)
    worker_in.bind(f'tcp://127.0.0.1:{WORKER_IN}')
    worker_in.setsockopt_string(zmq.SUBSCRIBE, '')
    worker_in.RCVTIMEO = 100
    # worker output - PUB
    worker_out = context.socket(zmq.PUB)
    worker_in.bind(f'tcp://127.0.0.1:{WORKER_OUT}')
    try:
        while True:
            try:
                message = worker_in.recv_string()
                if message.split(' ')[0] == "isprime":
                    num = int(message.split(' ')[1])
                    if my_isprime(num):
                        worker_in.send_string(f'{num} is prime')
                    else:
                        worker_in.send_string(f'{num} is not prime')

            except zmq.Again:
                pass
    except KeyboardInterrupt:
        print("Terminating client")
        sys.exit(0)


if __name__ == "__main__":
    checker(sys.argv)
    primer()
