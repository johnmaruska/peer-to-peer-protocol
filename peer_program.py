"""
    Peer Program for P2P File Transfer Protocol
    Handles both client and server portions of peer terminal.
"""

import socket
import sys
import threading
import time
import queue


class PeerServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        # TODO: wrap these in try blocks ?
        self.welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.welcome.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.welcome.bind((socket.gethostname(), self.port))

    def listen_to_client(self, client):
        try:
            while True:
                pass
                # TODO: receive messages and send data
                # P2P Protocol goes here.
        except KeyboardInterrupt:
            # client.close()
            pass

    def listen(self):
        print("PeerServer listen() entered")  # TODO: Remove post-debug
        self.welcome.listen(5)  # 5 maximum clients connected to each Peer.
        accepting = True
        while accepting:
            client, address = self.welcome.accept()
            # creates a new thread for each client that joins in
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()
            
    def quit(self):
        self.welcome.close()

    # TODO: implement send file as a server.
    def send_file(self):
        pass


def main():
    this_host = 'localhost'  # this system hostname
    this_port = 8888  # this system port number
    ts_host = '127.0.0.1'
    ts_port = 9999
    cmd_q = queue.Queue()
    ps = PeerServer(this_host, this_port)
    try:
        # Peer functions as a server for other peer-clients
        ps_t = threading.Thread(target=ps.listen)
        ps_t.start()
        # one thread for connection to the server
        ts_t = threading.Thread(name='track', target=track_comm, args=(ts_host, ts_port, cmd_q))
        ts_t.start()
        # one thread for raw input
        in_t = threading.Thread(name='input', target=commands, args=(cmd_q,))
        in_t.start()
    except RuntimeError:
        print("ERROR: Could not start all threads.")

    while ps_t.is_alive() and ts_t.is_alive() and in_t.is_alive():
        pass
    ps.quit()


def commands(cmd_q):
    try:  # loop input and enqueue command
        while True:
            time.sleep(0.1)
            cmd = input('$ ')
            cmd_args = cmd.split(' ')
            
            if cmd_args[0] == 'createtracker':
                if len(cmd_args) == 7:
                    cmd_q.put(cmd_args)
                else:
                    print('Improper number of arguments. Argument is formatted as:' \
                          'createtracker [filename] [filesize] [description] [md5]' \
                          '[ip-address] [port-number]')
            elif cmd_args[0] == 'updatetracker':
                if len(cmd_args) == 6:
                    cmd_q.put(cmd_args)
                else:
                    print("Improper number of arguments. Argument is formatted as: \
                           updatetracker [filename] [start_bytes] [end_bytes] \
                           [ip-address] [port-number]")
            elif cmd_args[0] == 'GET':
                if len(cmd_args) == 2:
                    cmd_q.put(cmd_args)
                else:
                    print("Improper number of arguments. Argument is formatted as: \
                           GET [filename]")
            elif cmd_args[0] == 'REQ' and cmd_args[1] == 'LIST':
                if len(cmd_args) == 2:
                    cmd_q.put(cmd_args)
                else:
                    print("Improper number of arguments. REQ LIST has no arguments.")
    except KeyboardInterrupt:
        pass


def cmd_tracker(server, cmd_q):
    msg = ""
    next_cmd = cmd_q.get()
    print(next_cmd)   # TODO: Remove post-debugging
    if next_cmd[0] == 'createtracker':
        filename = next_cmd[1]
        filesize = next_cmd[2]
        desc = next_cmd[3]
        md5 = next_cmd[4]
        ip_addr = next_cmd[5]
        port_num = next_cmd[6]   
        msg = "createtracker %s %s %s %s %s %s\n" % (filename, filesize, desc, md5,
                                                     ip_addr, port_num)
    elif next_cmd[0] == 'updatetracker':
        filename = next_cmd[1]
        start_bytes = next_cmd[2]
        end_bytes = next_cmd[3]
        ip_addr = next_cmd[4]
        port_num = next_cmd[5]
        msg = "updatetracker %s %s %s %s %s\n" % (filename, start_bytes,
                                                    end_bytes, ip_addr, port_num)
    elif next_cmd[0] == 'GET':
        filename = next_cmd[1]
        msg = "GET %s\n" % filename
    elif next_cmd[0] == 'REQ' and next_cmd[1] == 'LIST':
        msg = "REQ LIST\n"
    
    msg += ";endTCPmessage"
    
    if len(msg) > 0:
        msg = msg.encode("utf-8")
        server.sendall(msg)
        

def track_comm(host: str, port: int, cmd_q: queue.Queue):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    try:
        while True:
            cmd_tracker(server, cmd_q)
            recv_from_tracker(server)
    except KeyboardInterrupt:
        print("track_comm except KeyboardInterrupt entered")  # TODO: Remove post-debug
        server.close()


def recv_from_tracker(server: socket.socket):
    print("recv_from_tracker entered")  # TODO: Remove post-debug
    end_marker = ";endTCPmessage"
    total_msg = []
    while True:
        msg = (server.recv(1024)).decode("utf-8")
        if end_marker in msg:
            total_msg.append(msg[:msg.find(end_marker)])
            break
        total_msg.append(msg)

        """TODO: This section weirds me out. It's supposed to handle what happens on a split msg, but I'm not sure how
        it works."""
        if len(total_msg) > 1:
            # check if end of msg was split
            last_pair = total_msg[-2]+total_msg[-1]
            if end_marker in last_pair:
                total_msg[-2] = last_pair[:last_pair.find(end_marker)]
                total_msg.pop()
                break
    print(''.join(total_msg))
    print('recv_from_tracker exited')  # TODO: Remove post-debugging
        
if __name__ == "__main__":
    sys.exit(main())
