"""
    Peer Program for P2P File Transfer Protocol
    Handles both client and server portions of peer terminal.
"""

import math
import os
import random
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
        self.welcome.bind((self.host, self.port))

    def listen_to_client(self, client, address):
        try:
            while True:
                # TODO: receive messages and send data
                res = client.recv(1024).decode('utf-8')
                print(res)
                if res == 'FINISH':  # Disconnect when finished sending.
                    client.close()
                    break
                if res.split(' ')[0] == 'REQUEST':  # Send requested segment
                    # Don't have a filelist. Need solution.
                    # TODO: Change client side to send request in form REQUEST filename.ext #
                    file_name = res.split(' ')[1]
                    segment = res.split(' ')[2]
                    file_name = re.sub("\.[\w]+\Z", '', file_name)
                    file_seg = file_name + segment
                    file_size = str(os.path.getsize(file_seg))
                    client.send(file_size.encode('utf-8'))
                    output = open(file_seg, 'rb')
                    l = output.read(4096)
                    while l:
                        client.send(l)
                        l = output.read(4096)
                    output.close()
        finally:
            client.close()

    def listen(self):
        while True:
            self.welcome.listen(5)  # 5 maximum clients connected to each Peer.
            client, address = self.welcome.accept()
            # creates a new thread for each client that joins in
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()
            
    def quit(self):
        # TODO: Remove files from temporary folder.
        # TODO: Close all connected sockets
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


def main():
    this_host = 'localhost'  # this system hostname
    this_port = 61000  # this system port number
    ts_host = 'localhost'
    ts_port = 60000
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
            # TODO: Check contained md5 with protocol md5 for correctness.
            #
        except AttributeError:
            print("Improper arguments. GET requires a [filename].track")
    elif next_cmd == 'REQ LIST':
        msg = "REQ LIST\n"
    
    msg += ";endTCPmessage"
    
    if len(msg) > 0:
        msg = msg.encode("utf-8")
        server.sendall(msg)


def download_file(host, port: int):  # (filename) # Shifted sendfile_client.py into this function.
    # TODO: call GET, parse results, assign IP and port
    # get(filename)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    file_name = server.recv(1024).decode('utf-8')
    stri = server.recv(1024).decode('utf-8')
    segment_length = int(stri.split(' ')[1])
    nth_segment = random.randint(0, segment_length-1)
    count = 0
    while count < segment_length:
        filename = 'temp_client/output' + str(nth_segment)
        with open(filename, 'wb') as output:
            command = 'REQUEST' + file_name + str(nth_segment)
            server.send(command.encode())
            received = server.recv(4096)
            filesize = int(received.decode('utf-8'))
            total = 0
            while True:
                if total >= filesize:
                    break
                received = server.recv(4096)
                output.write(received)
                total += len(received)
            count += 1
            nth_segment += 1
            if nth_segment >= segment_length:
                nth_segment = 0
    server.send('FINISH'.encode())
    os.chdir('./temp_client/')
    filelist = os.listdir('.')
    with open(file_name, 'wb') as f:
        for name in filelist:
            file_input = open(name, 'rb')
            f.write(file_input.read())
            file_input.close()


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
    server_response = ''.join(total_msg)
    print(server_response)
    server_response = server_response.split('\n')
    if server_response[0] == 'REP GET BEGIN':
        for line in server_response:
            # (ip_addr:port_num:start_byte:end_byte:time
            m = re.match('([^:]+):([^:]+):([^:]+):([^:]+):([^:]+)', line)
            if m:
                ip_addr = m.group(1)
                port_num = int(m.group(2))
                download_file(ip_addr, port_num)
                break
    print('recv_from_tracker exited')  # TODO: Remove post-debugging
        
if __name__ == "__main__":
    sys.exit(main())
