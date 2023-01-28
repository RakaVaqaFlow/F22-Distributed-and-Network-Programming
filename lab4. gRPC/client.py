"""
DNP Lab 04: develop a server and a client using gRPC
Name Surname: Vagif Khalilov
Email: v.khalilov@innopolis.university
Group: BS20-SD-01
"""
from email import message
import grpc
import service_pb2 as pb2
import service_pb2_grpc as pb2_grpc
import sys

HOST = '127.0.0.1'
PORT = 5555

def get_error_message(error):
    if error == 'invalid arg':
        return 'Please, run the client again with arguments <host:port>\n example: python3 client.py 127.0.0.1:5555'
    elif error == 'invalid ip':
        return  'Invalid format of the server ip address.\n[0, 127].[0, 127].[0, 127].[0, 127] expected, example: 127.0.0.1'
    elif error == 'invalid port':
        return 'Invalid format of the port, integer in the range [1, 65535] is expected'
    else:
        return 'Invalid input'


# checker for the arguments of command line
def checker(args):
    #we can throw exceptions and use try catch case in the main instead of outputting an error to the console
    if len(args)!=2:
        print(get_error_message('invalid arg'))
        sys.exit(1)

    host = args[1].split(':')[0]
    num = host.split('.')

    # host checker
    if len(num) != 4:
        print()
        sys.exit(1)
    for i in num:
        try:
            if int(i)>127 or int(i)<0:
                print(get_error_message('invalid ip'))
                sys.exit(1)
        except:
            print(get_error_message('invalid ip'))
            sys.exit(1)

    # port checker
    try:
        port = int(args[1].split(':')[1])
    except:
        print(get_error_message('invalid port'))
        sys.exit(1)

    if port>65535 or port<1:
        print(get_error_message('invalid port'))
        sys.exit(1)

    global HOST
    HOST = args[1].split(':')[0]

    global PORT
    PORT = port
    

if __name__ == "__main__":

    # check the arguments
    checker(sys.argv)

    channel = grpc.insecure_channel(f"{HOST}:{PORT}")
    stub = pb2_grpc.serviceStub(channel)
    

    while True:
        try:
            message = input('> ')
            command = message.split(' ')[0] 
            data = ' '.join(message.split(' ')[1:])
            # reverse 
            if command == 'reverse':
                req = pb2.ReverseRequest(text=data)
                res = stub.ReverseText(req)
                print(res)

            # slpit
            elif command == 'split':
                req = pb2.SplitRequest(text=data)
                res = stub.SplitText(req)
                print(res)

            # isprime
            elif command == 'isprime':

                # request generator 
                def gen_req(numbers):
                    for number in numbers:
                        yield pb2.IsprimeRequest(num=number)
                
                data = [int(x) for x in data.split(' ')]
                for resp in stub.IsPrimeNumber(gen_req(data)):
                    print(resp.res)

            elif command == 'exit':
                raise KeyboardInterrupt
            else: 
                print("Please, try again")
        except KeyboardInterrupt:
            print("Shutting down")
            exit(0)
    