"""
--------
Node
--------

DNP Lab 5: Chord
Students: Vagif Khalilov, Artem Murashko
Emails: v.khalilov@innopolis.university, ar.murashko@innopolis.univeristy
Group: BS20-SD-01
"""

# Imports

import chord_pb2 as pb2
import chord_pb2_grpc as pb2_grpc

import grpc
import sys
import signal
import time
import zlib

from concurrent import futures
from threading import Thread

# Config

REGISTRY_HOST = '127.0.0.1'
REGISTRY_PORT = '5555'

HOST = '127.0.0.1'
PORT = '5001'

FETCH_FINGER_TABLE_TIME_INTERVAL = 10.0
REGISTRY_CONNECTION_TIMEOUT = 1.5
REGISTRY_RESPONSE_TIMEOUT = 0.5
NODE_CONNECTION_TIMEOUT = 1.5
NODE_RESPONSE_TIMEOUT = 1

MAX_WORKERS = 10

registry_channel = None
registry_stub = None

node_handler = None

# Variables

node_id = None
key_size = 5
predecessor_id = None

finger_table = {}
node_dict = {}


# Helper

def terminate(message, closure=None):
    log(message)
    if closure is not None:
        closure()
    sys.exit()


def log(message, end="\n"):
    print(message, end=end)


def get_error_message(error):
    if error == 'invalid arg':
        return 'Please, run the node again with argument <registry-ipaddr>:<registry-port> <ipaddr>:<port>\n ' \
               'example: python3 Node.py 127.0.0.1:5000 127.0.0.1:5001'
    elif error == 'invalid port':
        return 'Invalid format of the port, integer in the range [1, 65535] is expected'
    elif error == 'invalid ip':
        return 'Invalid format of the ip address.\n[0,127].[0,127].[0,127].[0,127] expected, example:127.0.0.1'
    else:
        return 'Invalid input'

# ip address  checker
def validate_ipaddr(ipaddr):
    num = ipaddr.split('.')
    if len(num) != 4:
        return False, get_error_message('invalid arg')
    for i in num:
        try:
            if int(i) > 127 or int(i) < 0:
                return False, get_error_message('invalid ip')
        except:
            return False, get_error_message('invalid ip')
    return True, ipaddr

# port checker
def validate_port(port):
    if not port.isdigit():
        return False, get_error_message('invalid port')

    if int(port) > 65535 or int(port) < 1:
        return False, get_error_message('invalid port')

    return True, port

# socket address checker
def validate_socket_address(socket_addr):
    # checking for <ip address>:<port>
    if len(socket_addr.split(':')) != 2:
        return False, get_error_message('invalid arg')

    # ip address checking 
    ipaddr = socket_addr.split(':')[0]
    valid, res = validate_ipaddr(ipaddr)
    if not valid:
        return valid, res

    # port checking
    port = socket_addr.split(':')[1]
    valid, res = validate_port(port)
    if not valid:
        return valid, res
    
    return True, socket_addr

def parse_arg(args):
    if len(args) != 3:
        terminate(get_error_message('invalid arg'))

    # Registry socket address checking
    valid, res = validate_socket_address(args[1])
    if not valid:
        terminate(res)

    registry_ip_address = args[1].split(':')[0]
    registry_port = args[1].split(':')[1]

    global REGISTRY_HOST
    global REGISTRY_PORT

    REGISTRY_HOST = registry_ip_address
    REGISTRY_PORT = registry_port

    # Node socket address checking
    valid, res = validate_socket_address(args[2])
    if not valid:
        terminate(res)

    node_ip_address = args[2].split(':')[0]
    node_port = args[2].split(':')[1]

    global HOST
    global PORT

    HOST = node_ip_address
    PORT = node_port 


# Node handler

class NodeHandler(pb2_grpc.NodeServiceServicer):
    next_node_channel = None
    next_node_stub = None

    # RPC Functions

    # This function is called by the client. It should just return the current finger table.
    def get_finger_table(self, request, context):
        log('Get finger table')
        fetch_finger_table()

        finger_table_message = []
        for successor_id, socket_addr in finger_table.items():
            ipaddr, port = socket_addr
            finger_table_message.append(pb2.Node(id=successor_id, socket_addr=f"{ipaddr}:{port}"))

        return pb2.GetFingerTableReply(node_id=node_id, finger_table=finger_table_message)

    # Saves the key and the text on the corresponding node
    def save(self, request, context):
        fetch_finger_table()

        key = request.key
        text = request.text

        hashed_key = hash_key(key)
        log(f'Save: {hashed_key} | {key}')

        next_id = self._find_next_node_id(hashed_key)
        if next_id == -1:
            return pb2.SaveReply(result=False, message=f'Something go wrong, annot find next node.')
        elif next_id == node_id:
            if node_dict.get(hashed_key) is not None:
                return pb2.SaveReply(result=False, message=f'Collision. Hash of {key} already exist in node {node_id}')

            node_dict[hashed_key] = (key, text)
            return pb2.SaveReply(result=True, message=f'{key} is saved in node {node_id}')

        return self.send_save_to_next_node(next_id, key, text)

    # Similar to the save method. But removes the key and the text from the corresponding node.
    def remove(self, request, context):
        fetch_finger_table()

        key = request.key

        hashed_key = hash_key(key)
        log(f'Delete: {hashed_key} | {key}')

        next_id = self._find_next_node_id(hashed_key)
        if next_id == -1:
            return pb2.RemoveReply(result=False, message=f'Something go wrong, cannot find next node.')
        elif next_id == node_id:
            if node_dict.get(hashed_key) is None:
                return pb2.RemoveReply(result=False, message=f'{key} is not exist')

            node_dict.pop(hashed_key)
            return pb2.RemoveReply(result=True, message=f'{key} is removed from node {node_id}')

        return self._send_remove_to_next_node(next_id, key)

    # Find the node, the key and the text should be saved on.
    def find(self, request, context):
        fetch_finger_table()

        key = request.key

        hashed_key = hash_key(key)
        log(f'Find: {hashed_key} | {key}')

        next_id = self._find_next_node_id(hashed_key)
        if next_id == -1:
            return pb2.FindReply(result=False, message=f'Something go wrong, cannot find next node.')
        elif next_id == node_id:
            if node_dict.get(hashed_key) is None:
                return pb2.FindReply(result=False, message=f'{key} is not exist')

            return pb2.FindReply(result=True, message=f'{key} is storing at node {node_id}, address {HOST}:{PORT}')

        return self._send_find_to_next_node(next_id, key)

    # Find data which should store on predecessor and return it.
    def get_data_from_successor(self, request, context):
        fetch_finger_table()

        messages = []
        for hashed_key, data in list(node_dict.items()):
            key, text = data

            # If current hashed_key should be store in current node
            if predecessor_id < hashed_key <= node_id or \
                    hashed_key <= node_id < predecessor_id or \
                    node_id < predecessor_id < hashed_key or \
                    node_id == hashed_key:
                continue

            node_dict.pop(hashed_key)
            messages.append(pb2.SaveRequest(key=key, text=text))

        return pb2.GetDataFromSuccessorReply(data=messages)

    # Helper Methods

    def _find_next_node_id(self, key):
        if predecessor_id < key <= node_id or key <= node_id < predecessor_id or node_id < predecessor_id < key or node_id == key:
            return node_id

        successor_id = get_current_node_successor_id()
        if node_id < key <= successor_id or successor_id < node_id < key or key <= successor_id < node_id or successor_id == key:
            return successor_id

        next_id = - 1

        # If we have ids, for example: 2, 23, 30, and key_size equal to 5, I will make an array
        # equal to 2, 23, 30, (2 + 32), (23 + 32), (30 + 32) = 2, 23, 30, 34, 55, 62 to find appropriate
        # position for the key.
        dict_list = list(finger_table.items())
        dict_list.sort()
        mapped_dict_list = list(map(lambda x: [x[0] + 2 ** key_size, x[1]], dict_list))
        dict_list += mapped_dict_list

        for i in range(0, len(dict_list) - 1):
            if dict_list[i][0] <= key < dict_list[i + 1][0] or dict_list[i][0] <= key + 2 ** key_size < \
                    dict_list[i + 1][0]:
                next_id = dict_list[i][0]
                break

        return -1 if next_id == -1 else next_id % 32

    def _connect_to_next_node(self, next_node_id):
        ipaddr, port = finger_table[next_node_id]

        self.next_node_channel = grpc.insecure_channel(f"{ipaddr}:{port}")
        try:
            grpc.channel_ready_future(self.next_node_channel).result(timeout=NODE_CONNECTION_TIMEOUT)
        except:
            self._close_next_node_connection()
        else:
            self.next_node_stub = pb2_grpc.NodeServiceStub(self.next_node_channel)

    def send_save_to_next_node(self, next_node_id, key, text):
        self._connect_to_next_node(next_node_id)

        if self.next_node_stub is None:
            return pb2.SaveReply(result=False, message=f'Unable to connect to node {next_node_id}')

        message = pb2.SaveRequest(key=key, text=text)
        try:
            get_save_key_response = self.next_node_stub.save(message, timeout=NODE_RESPONSE_TIMEOUT)
        except grpc.RpcError:
            self._close_next_node_connection()
            return pb2.SaveReply(result=False, message=f'Response timeout of node {next_node_id} exceeded.')

        self.next_node_channel.close()
        self._close_next_node_connection()

        return get_save_key_response

    def _send_remove_to_next_node(self, next_node_id, key):
        self._connect_to_next_node(next_node_id)

        if self.next_node_stub is None:
            return pb2.RemoveReply(result=False, message=f'Unable to connect to node {next_node_id}')

        message = pb2.RemoveRequest(key=key)
        try:
            get_remove_key_response = self.next_node_stub.remove(message, timeout=NODE_RESPONSE_TIMEOUT)
        except grpc.RpcError:
            self._close_next_node_connection()
            return pb2.RemoveReply(result=False, message=f'Response timeout of node {next_node_id} exceeded.')

        self.next_node_channel.close()
        self._close_next_node_connection()

        return get_remove_key_response

    def _send_find_to_next_node(self, next_node_id, key):
        self._connect_to_next_node(next_node_id)

        if self.next_node_stub is None:
            return pb2.FindReply(result=False, message=f'Unable to connect to node {next_node_id}')

        message = pb2.FindRequest(key=key)
        try:
            get_find_key_response = self.next_node_stub.find(message, timeout=NODE_RESPONSE_TIMEOUT)
        except grpc.RpcError:
            self._close_next_node_connection()
            return pb2.FindReply(result=False, message=f'Response timeout of node {next_node_id} exceeded.')

        self.next_node_channel.close()
        self._close_next_node_connection()

        return get_find_key_response

    def _close_next_node_connection(self):
        self.next_node_channel = None
        self.next_node_stub = None


def fetch_finger_table():
    message = pb2.PopulateFingerTableRequest(node_id=node_id)
    try:
        populate_finger_table_response = registry_stub.populate_finger_table(message, timeout=REGISTRY_RESPONSE_TIMEOUT)
    except grpc.RpcError:
        terminate("Registry response timeout exceeded. Close the connection.")

    finger_table_message = populate_finger_table_response.finger_table
    new_finger_table = {}

    for row in finger_table_message:
        ipaddr = row.socket_addr.split(':')[0]
        port = row.socket_addr.split(':')[1]
        new_finger_table[row.id] = (ipaddr, port)

    global predecessor_id
    predecessor_id = populate_finger_table_response.node_id

    global finger_table
    finger_table = new_finger_table

    # log(f"Predecessor: {predecessor_id}")
    # log(f"Finger table: {finger_table}")


def get_current_node_successor_id():
    all_id = finger_table.keys()

    min_delta = 2 ** key_size
    successor_id = -1
    min_id = 2 ** key_size

    # Find the closest id to the given one and having the greater value
    for current_id in all_id:
        delta = current_id - node_id
        min_id = min(min_id, current_id)
        if 0 < delta < min_delta:
            min_delta = delta
            successor_id = current_id

    # If no successor found, set it to the smallest id in the chord
    if successor_id == -1:
        successor_id = min_id

    return successor_id


def hash_key(key):
    hash_value = zlib.adler32(key.encode())
    target_id = hash_value % 2 ** key_size
    return target_id


def start_fetching_finger_table():
    while True:
        fetch_finger_table()
        time.sleep(FETCH_FINGER_TABLE_TIME_INTERVAL)


def register_in_chord():
    message = pb2.RegisterRequest(ipaddr=HOST, port=PORT)
    try:
        registry_response = registry_stub.register(message, timeout=REGISTRY_RESPONSE_TIMEOUT)
    except grpc.RpcError:
        terminate("Registry response timeout exceeded. Close the connection.")

    # Fail
    if registry_response.node_id == '-1':
        terminate(f"Cannot register node: {registry_response.message}")

    # Success
    global node_id
    node_id = int(registry_response.node_id)

    global key_size
    key_size = int(registry_response.message)

    log(f"Registered in chord with id = {node_id}")

    # Fetch finger table for the first time
    fetch_finger_table()

    # Get data from successor node
    successor = get_current_node_successor_id()

    # Nothing to fetch if we have 1 node in chord
    if node_id == successor:
        return

    ipaddr, port = finger_table[successor]

    # Connect to successor
    next_node_channel = grpc.insecure_channel(f"{ipaddr}:{port}")
    try:
        grpc.channel_ready_future(next_node_channel).result(timeout=NODE_CONNECTION_TIMEOUT)
    except:
        log("Cannot connect to successor to request data")
        return
    next_node_stub = pb2_grpc.NodeServiceStub(next_node_channel)

    # Make request
    message = pb2.GetDataFromSuccessorRequest()
    try:
        response = next_node_stub.get_data_from_successor(message, timeout=NODE_RESPONSE_TIMEOUT)
    except grpc.RpcError as e:
        log("Successor node response timeout exceeded. Close the connection.")
        return

    # Add data to dictionary
    for data in response.data:
        node_dict[hash_key(data.key)] = (data.key, data.text)


def deregister_in_chord():
    if node_id is None:
        terminate("Node is not registered yet")

    message = pb2.DeregisterRequest(node_id=node_id)
    try:
        registry_response = registry_stub.deregister(message, timeout=REGISTRY_RESPONSE_TIMEOUT)
    except grpc.RpcError:
        terminate("Registry response timeout exceeded. Close the connection.")

    successor_id = get_current_node_successor_id()

    # Nothing to transfer if we have 1 node in chord
    if successor_id == node_id:
        return

    for hashed_key, value in list(node_dict.items()):
        key, text = value
        node_handler.send_save_to_next_node(successor_id, str(key), text)

    registry_channel.close()
    if registry_response.result:  # success
        terminate(registry_response.message)
    else:  # error
        terminate(registry_response.message)


def connect_to_registry():
    global registry_channel
    global registry_stub

    registry_channel = grpc.insecure_channel(f"{REGISTRY_HOST}:{REGISTRY_PORT}")
    try:
        grpc.channel_ready_future(registry_channel).result(timeout=REGISTRY_CONNECTION_TIMEOUT)
    except grpc.FutureTimeoutError:
        terminate("Cannot connect to the registry.")
    else:
        registry_stub = pb2_grpc.RegistryServiceStub(registry_channel)


def start_node_server():
    global node_handler
    node_handler = NodeHandler()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKERS))
    pb2_grpc.add_NodeServiceServicer_to_server(node_handler, server)
    server.add_insecure_port(f"{HOST}:{PORT}")
    server.start()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt as keys:
        terminate(f'{keys} was pressed, terminating server.', deregister_in_chord)


# Init


def start_node():
    # Connect to registry
    connect_to_registry()

    # Try to register self in the chord
    register_in_chord()

    # Start thread to get finger_table every 1 second
    fetcher_worker_thread = Thread(target=start_fetching_finger_table, args=(), daemon=True)
    fetcher_worker_thread.start()

    # Start Node server
    server_worker_thread = Thread(target=start_node_server, args=(), daemon=True)
    server_worker_thread.start()

    # Start console input handling
    while True:
        message = input('> ')

        if message == 'quit':
            deregister_in_chord()
        else:
            log("Unknown command.")
            log("Available commands: \n (1) quit - deregister node and terminate the program.")


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.default_int_handler)

    parse_arg(sys.argv)

    try:
        start_node()
    except KeyboardInterrupt as keys:
        terminate(f'{keys} was pressed, terminating server.', deregister_in_chord)
