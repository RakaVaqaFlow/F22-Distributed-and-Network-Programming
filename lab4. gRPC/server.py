"""
DNP Lab 04: develop a server and a client using gRPC
Name Surname: Vagif Khalilov
Email: v.khalilov@innopolis.university
Group: BS20-SD-01
"""
import service_pb2_grpc as pb2_grpc
import service_pb2 as pb2
import grpc
import sys
from concurrent import futures

PORT = 5555

# get error message for checker function
def get_error_message(error):
    if error == 'invalid arg':
        return 'Please, run the server again with argument <port>\n example: python3 server.py 5555'
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
    
    # port checker
    try:
        port = int(args[1])
    except:
        print(get_error_message('invalid port'))
        sys.exit(1)

    if port>65535 or port<1:
        print(get_error_message('invalid port'))
        sys.exit(1)

    global PORT
    PORT = port

# reverse text function
def reverse_text(text):
    return text[::-1]

# split text function
def split_text(text):
    return text.split(' ')

# isprime number function
def my_isprime(num):
    if num == 1:
        return False

    for i in range(2, num):
        if num % i == 0:
            return False

    return True

# request handler
class Handler(pb2_grpc.serviceServicer):

    # reverse text
    def ReverseText(self, request, context):
        text = request.text
        reply = {"text": reverse_text(text)}
        return pb2.ReverseResponse(**reply)
    
    # split text 
    def SplitText(self, request, context):
        text = request.text
        splitText = split_text(text)
        reply = {"size": len(splitText), "part": splitText}
        return pb2.SplitResponse(**reply)


    # isprime number
    def IsPrimeNumber(self, request_iterator, context):
        for req in request_iterator:
            if my_isprime(req.num):
                yield pb2.IsprimeResponse(res=f"{req.num} is prime")
            else:
                yield pb2.IsprimeResponse(res=f"{req.num} is not prime")



if __name__ == "__main__":

    # check the arguments
    checker(sys.argv)

    # server settings
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_serviceServicer_to_server(Handler(), server)
    server.add_insecure_port(f"127.0.0.1:{PORT}")

    # starting server
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Shutting down")