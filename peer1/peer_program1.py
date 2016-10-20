"""
    Peer Program for P2P File Transfer Protocol
    Handles both client and server portions of peer terminal.
"""

import hashlib
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
            # filename = client.recv(1024).decode()
            filename = recv_from(client).lstrip('REQUEST ')
            filelist = split_file(filename, 10)
            segment_number = len(filelist)
            print(segment_number)
            msg = "SEGMENT " + str(segment_number)
            # client.send(msg.encode())
            encode_and_send(client, msg)
            nth_segment = 0
            while True:
                # TODO: receive messages and send data
                # res = client.recv(1024)
                res = recv_from(client)
                print(res)
                if res == "FINISH":
                    break
                if res.split(' ')[0] == "REQUEST":
                    res_list = res.split(' ')
                    print(int(res_list[1]))
                    print("Send File " + res_list[1])
                    # FILE SIZE
                    file_size = os.path.getsize(filelist[int(res_list[1])])
                    file_size = str(file_size)
                    # client.send(file_size.encode())
                    encode_and_send(client, file_size)
                    output = open(filelist[int(res_list[1])], "rb")
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
        # createtracker filename filesize description md5 ip_addr port_num
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
            split_file(filename, 10)  # Said maximum chunk size 1KB?
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


def split_file(filename, number_of_file):
    # Make split function irrelevant to OS#Make split function irrelevant to OS
    size = os.path.getsize(filename)
    folder_name = hashlib.sha224(filename.encode()).hexdigest()
    if not os.path.exists("./" + folder_name):
        os.mkdir(folder_name)
    with open(filename, "rb") as f:
        n = size // number_of_file
        os.chdir(folder_name)
        for i in range(0, number_of_file):
            if i == number_of_file - 1:
                readsize = size - (number_of_file - 1) * n
            else:
                readsize = n
            input = open("input" + str(i), "wb")
            input.write(f.read(readsize))
            input.close()
    filelist = os.listdir('.')
    return filelist


def download_file(host, port: int, filename):  # (filename) # Shifted sendfile_client.py into this function.
    # TODO: call GET, parse results, assign IP and port
    print('Downloading file.')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    encode_and_send(server, ('REQUEST %s' % filename))  # TODO: Needs second argument: segment
    # How does the server know to send this information?
    # file_name = server.recv(1024).decode('utf-8')
    if not os.path.exists("./temp_client"):
        os.mkdir("./temp_client/")
    else:
        clearfile = os.listdir("./temp_client/")
        print(clearfile)
        for s in clearfile:
            os.remove("./temp_client/" + s)
    segment_name = recv_from(server)
    print('file_name: %s' % segment_name)
    # stri = server.recv(1024).decode('utf-8')
    stri = recv_from(server)
    print('stri: %s' % stri)
    print(len(stri.split(' ')))
    segment_length = int(stri.split(' ')[1])
    print('Segment Length: %s' % segment_length)
    nth_segment = random.randint(0, segment_length-1)
    count = 0
    while count < segment_length:
        print('Segment count: %s' % count)
        filename = 'temp_client/output' + str(nth_segment)
        with open(filename, 'wb') as output:
            print('Writing to %s' % filename)
            command = 'REQUEST' + segment_name + str(nth_segment)
            encode_and_send(server, command)
            # received = server.recv(4096)
            received = recv_from(server)
            filesize = int(received.decode('utf-8'))
            total = 0
            while True:
                if total >= filesize:
                    break
                received = server.recv(4096)
                #received = recv_from(server)
                output.write(received)
                total += len(received)
            count += 1
            nth_segment += 1
            if nth_segment >= segment_length:
                nth_segment = 0
    encode_and_send(server, 'FINISH')
    os.chdir('./temp_client/')
    filelist = os.listdir('.')
    with open(segment_name, 'wb') as f:
        print('Writing to %s' % segment_name)
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
    server_response = recv_from(server)
    print(server_response)
    server_response = server_response.split('\n')
    if server_response[0] == 'REP GET BEGIN':
        for line in server_response:
            if 'Filename: ' in line:
                filename = line.lstrip('Filename: ')
            # (ip_addr:port_num:start_byte:end_byte:time
            m = re.match('([^:]+):([^:]+):([^:]+):([^:]+):([^:]+)', line)
            if m:
                ip_addr = m.group(1)
                port_num = int(m.group(2))
                print('Match found: %s %s' % (ip_addr, port_num))
                download_file(ip_addr, port_num, filename)
                break
    print('recv_from_tracker exited')  # TODO: Remove post-debugging


def recv_from(server: socket.socket):
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
            last_pair = total_msg[-2] + total_msg[-1]
            if end_marker in last_pair:
                total_msg[-2] = last_pair[:last_pair.find(end_marker)]
                total_msg.pop()
                break
    return ''.join(total_msg)


def encode_and_send(client: socket.socket, msg: str):
    msg += ';endTCPmessage'
    client.send(msg.encode('utf-8'))

if __name__ == "__main__":
    sys.exit(main())
