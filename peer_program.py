"""
    Peer Program for P2P File Transfer Protocol
    Handles both client and server portions of peer terminal.
"""

import math
import os
import re
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
        self.welcome.listen(5)  # 5 maximum clients connected to each Peer.
        accepting = True
        while accepting:
            client, address = self.welcome.accept()
            # creates a new thread for each client that joins in
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()
            
    def quit(self):
        # TODO: Remove files from temporary folder.
        self.welcome.close()

    def split_file(self, file_name, segment_size):
        # Make split function irrelevant to OS
        total_size = os.path.getsize(file_name)
        file_list = []
        with open(file_name, "rb") as f:
            total_segments = math.ceil(total_size / segment_size)
            for i in range(0, total_segments):
                if i == 2:
                    readsize = total_size - (total_segments - 1) * segment_size
                else:
                    readsize = segment_size
                file_i = open("input" + str(i), "wb")
                file_i.write(f.read(readsize))
                file_i.close()
                file_list.append(file_i)
        return file_list

    def send_segment(self, filename, client: socket.socket):
        # Receive a status command: FINISH, REQUEST, or DONE
        # REQUEST: Requests a file.
        while True:
            res = client.recv(1024).decode('utf-8')
            if res == 'FINISH':
                break
            if res.split(' ')[0] == 'REQUEST':
                file_size = str(os.path.getsize(filename))
                client.send(file_size.encode('utf-8'))
                output = open(filename, 'rb')
                l = output.read(4096)
                while l:
                    client.send(l)
                    l = output.read(4096)
                output.close()


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
        while ps_t.is_alive() and ts_t.is_alive() and in_t.is_alive():
            pass
    except RuntimeError:
        print("ERROR: Could not start all threads.")

    ps.quit()


def commands(cmd_q):
    try:  # loop input and enqueue command
        while True:
            time.sleep(0.1)
            cmd = input('$ ')
            try:
                cmd_args = re.match('^([^ ]+) (.*)', cmd)
                accepted_commands = ['createtracker', 'updatetracker', 'GET']
                if cmd_args.group(1) in accepted_commands:
                    cmd_q.put(cmd)
                elif re.match('REQ LIST', cmd):
                    cmd_q.put('REQ LIST')
            except AttributeError:
                print('Not a valid command.')
    except KeyboardInterrupt:
        pass


def cmd_tracker(server, cmd_q):
    msg = ""
    next_cmd = cmd_q.get()
    print(next_cmd)   # TODO: Remove post-debugging
    if re.match('createtracker .*', next_cmd):
        m = re.match('(createtracker) ([^ ]+) ([^ ]+) (".*") ([^ ]+) ([^ ]+)'
                     ' ([^ ]+)', next_cmd)
        try:
            filename = m.group(2)
            filesize = m.group(3)
            desc = m.group(4)
            md5 = m.group(5)
            ip_addr = m.group(6)
            port_num = m.group(7)
            msg = "createtracker %s %s %s %s %s %s\n" % (filename, filesize, desc, md5,
                                                         ip_addr, port_num)
        except AttributeError:
            print('Improper number of arguments. createtracker is formatted as: '
                  'createtracker [filename] [filesize] [description] [md5] [ip-address] '
                  '[port-number]')

    elif re.match('updatetracker .*', next_cmd):
        m = re.match('(updatetracker) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+)', next_cmd)
        try:
            filename = m.group(2)
            start_bytes = m.group(3)
            end_bytes = m.group(4)
            ip_addr = m.group(5)
            port_num = m.group(6)
            msg = "updatetracker %s %s %s %s %s\n" % (filename, start_bytes,
                                                      end_bytes, ip_addr, port_num)
        except AttributeError:
            print('Improper number of arguments. Argument is formatted as: '
                  'updatetracker [filename] [start_bytes] [end_bytes] [ip-address] '
                  '[port-number]')

    elif re.match('GET .*', next_cmd):
        m = re.match('GET ([^ ]+\.track)', next_cmd)
        try:
            filename = m.group(1)
            msg = "GET %s\n" % filename
        except AttributeError:
            print("Improper arguments. GET requires a [filename].track")
    elif next_cmd == 'REQ LIST':
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

        # TODO: Weird section. Supposed to handle split msg, not sure how it works
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
