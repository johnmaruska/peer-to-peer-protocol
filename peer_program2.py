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
            filename = recv_from(client)
            filename = filename[8:]
            filelist = split_file(filename, 10)
            segment_number = len(filelist)
            msg = "SEGMENT " + str(segment_number)
            encode_and_send(client, msg)
            while True:
                # TODO: receive messages and send data
                res = recv_from(client)
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
        except ConnectionResetError:
            print("ConnectionResetError: Connection forcibly closed by remote host.")
        except Exception as e:
            print("Unexpected exception: %s" % e)
            raise e
        finally:
            client.close()

    def listen(self):
        self.welcome.listen(5)
        while True:
            try:
                (client, address) = self.welcome.accept()
                # creates a new thread for each client that joins in
                threading.Thread(target=self.listen_to_client, args=(client, address)).start()
            except Exception as e:
                pass
    def quit(self):
        # TODO: Remove files from temporary folder.
        # TODO: Close all connected sockets
        self.welcome.close()

THIS_PORT = 62000
THIS_HOST = "localhost"
cmd_q = queue.Queue()

def main():
    ts_host = 'localhost'
    ts_port = 60000

    ps = PeerServer(THIS_HOST, THIS_PORT)
    try:
        # Peer functions as a server for other peer-clients
        ps_t = threading.Thread(target=ps.listen)
        ps_t.start()
        # one thread for connection to the server
        ts_t = threading.Thread(name='track', target=track_comm, args=(ts_host, ts_port))
        ts_t.start()
        # one thread for raw input
        in_t = threading.Thread(name='input', target=commands, args=())
        in_t.start()
        while ps_t.is_alive() and ts_t.is_alive() and in_t.is_alive():
            pass
    except RuntimeError:
        print("ERROR: Could not start all threads.")
    finally:
        # TODO: Check and see if killing threads or otherwise stopping them
        # is a possibility and required here.
        ps.quit()


def commands():
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

def hashfile(afile, blocksize=65536):
    f = open(afile, 'rb')
    buf = f.read(blocksize)
    while len(buf) > 0:
        hashlib.md5().update(buf)
        buf = f.read(blocksize)
    return hashlib.md5().hexdigest()


def createtracker(filename, desc):
    if os.path.isfile(filename):
        size = os.path.getsize(filename)
        md5 = hashfile(filename)
        ip = THIS_HOST
        port = THIS_PORT
        return 'createtracker %s %s %s %s %s %s' % (filename, size, desc, md5, ip, port)
    else:
        return 'createtracker fail'


def cmd_tracker(server):
    msg = ""
    next_cmd = cmd_q.get()
    print(next_cmd)   # TODO: Remove post-debugging
    if re.match('createtracker .*', next_cmd):
        # createtracker filename description
        m = re.match('(createtracker) ([^ ]+) (".*")', next_cmd)
        try:
            filename = m.group(2)
            desc = m.group(3)
            msg = createtracker(filename, desc)
            if os.path.isfile(filename):
                split_file(filename, 10)  # TODO: Change to be chunk-size not number of files?
            else:
                print("Cannot create tracker. This file does not exist.")
        except AttributeError:
            print('Improper number of arguments. createtracker is formatted as: '
                  'createtracker [filename] [description]')

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
        msg = next_cmd

    elif next_cmd == 'REQ LIST' or next_cmd == 'LIST':
        msg = "REQ LIST\n"

    msg += ";endTCPmessage"

    if len(msg) > 0:
        msg = msg.encode("utf-8")
        server.sendall(msg)



def split_file(filename, number_of_file):
    # Make split function irrelevant to OS#Make split function irrelevant to OS
    try:
        size = os.path.getsize(filename)
    except FileNotFoundError:  # Sometimes randomly doesn't find the file - try again.
        try:
            size = os.path.getsize(filename)
        except FileNotFoundError:
            print("FileNotFoundError: The system cannot find the file specified: %s" % filename)
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
    for i in range(0, len(filelist)):
        filelist[i] = folder_name + "/" + filelist[i]
    os.chdir("../")

    return filelist


def download_file(trackserver: socket.socket, host: str, port: int, original_filename): # (filename) # Shifted sendfile_client.py into this function.
    # TODO: call GET, parse results, assign IP and port
    start_bytes = 0
    end_bytes = 0
    print('Downloading file.')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    encode_and_send(server, ('REQUEST %s' % original_filename))  # TODO: Needs second argument: segment
    print("REQUEST %s" % original_filename)
    folder_name = "./temp_client/" + hashlib.sha224(original_filename.encode()).hexdigest() + "/"
    # How does the server know to send this information?
    # file_name = server.recv(1024).decode('utf-8')
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    else:
        clearfile = os.listdir(folder_name)
        print(clearfile)
        for s in clearfile:
            os.remove(folder_name + s)
    segment_name = recv_from(server)
    segment_length = int(segment_name.split(' ')[1])
    print("SEGMENT_NAME:" + segment_name)
    nth_segment = random.randint(0, segment_length-1)
    count = 0
    while count < segment_length:
        # Download file part
        print('Segment count: %s' % count)
        filename = folder_name + 'output' + str(nth_segment)
        with open(filename, 'wb') as output:
            print('Writing to %s' % filename)
            command = 'REQUEST %s' % str(nth_segment)
            encode_and_send(server, command)
            # received = server.recv(4096)
            received = recv_from(server)
            filesize = int(received)
            total = 0
            while True:
                if total >= filesize:
                    break
                received = server.recv(4096)
                # received = recv_from(server)
                output.write(received)
                total += len(received)
            count += 1
            nth_segment += 1
            if nth_segment >= segment_length:
                nth_segment = 0
        #UpdateTracker Part

        start_bytes = end_bytes
        end_bytes = start_bytes + total
        ip_addr = 'localhost'
        port_num = 62000
        msg = "updatetracker %s %s %s %s %s\n" % (original_filename, start_bytes,
                                                      end_bytes, ip_addr, port_num)
        cmd_q.put(msg)

    encode_and_send(server, 'FINISH')
    filelist = os.listdir(folder_name)
    with open(original_filename, 'wb') as f:
        print('Writing to %s' % original_filename)
        for name in filelist:
            name = folder_name + name
            file_input = open(name, 'rb')
            f.write(file_input.read())
            file_input.close()

def download_file_segment(host: str, port: int, original_filename:str, segment:int, start_bytes:int, end_bytes:int):
    print(host, port)
    print('Downloading file.')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    encode_and_send(server, ('REQUEST %s' % original_filename))  # TODO: Needs second argument: segment
    print("REQUEST %s" % original_filename)
    folder_name = "./temp_client/" + hashlib.sha224(original_filename.encode()).hexdigest() + "/"
    # How does the server know to send this information?
    # file_name = server.recv(1024).decode('utf-8')
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    segment_name = recv_from(server)
    segment_length = int(segment_name.split(' ')[1])
    nth_segment = segment
    count = 0
    # Download file part
    filename = folder_name + 'output' + str(nth_segment)
    with open(filename, 'wb') as output:
        print('Writing to %s' % filename)
        command = 'REQUEST %s' % str(nth_segment)
        encode_and_send(server, command)
        # received = server.recv(4096)
        received = recv_from(server)
        filesize = int(received)
        total = 0
        while True:
            if total >= filesize:
                break
            received = server.recv(4096)
            # received = recv_from(server)
            output.write(received)
            total += len(received)
        # UpdateTracker Part

        ip_addr = 'localhost'
        port_num = 62000
        msg = "updatetracker %s %s %s %s %s\n" % (original_filename, start_bytes,
                                                  end_bytes, ip_addr, port_num)
        cmd_q.put(msg)

    encode_and_send(server, 'FINISH')
    server.close()


def track_comm(host: str, port: int):
    while True:
        try:
            if not cmd_q.empty():
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.connect((host, port))
                cmd_tracker(server)
                recv_from_tracker(server)
                server.close()
        except ConnectionRefusedError:
            print("ConnectionRefusedError: Tracking server currently down. Try again later.")
            break

def recv_from_tracker(server: socket.socket):
    print("recv_from_tracker entered")  # TODO: Remove post-debug
    server_response = recv_from(server)
    print(server_response)
    server_response = server_response.split('\n')
    file_list = []
    filesize = 0
    filename = ""
    if server_response[0] == 'REP GET BEGIN':
        for line in server_response:
            if 'Filename: ' in line:
                filename = line[10:] #TODO: the number is weird.
                file_name = filename
                print("IN IF FILENAME: ", filename)
            if 'Filesize: ' in line:
                filesize = int(line[10:])
            # (ip_addr:port_num:start_byte:end_byte:time
            m = re.match('([^:]+):([^:]+):([^:]+):([^:]+):([^:]+)', line)
            if m:
                file_tuple = (m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5))
                file_list.append(file_tuple)
                #threading.Thread(target=download_file_segment, args=(server, ip_addr, port_num, filename, segment, start_bytes, end_bytes)).start()
                break
    segment = 10 #TODO: change the segment based on configure file
    for i in range(0, segment):
        start_bytes = filesize // segment * i
        if i == segment-1:
            end_bytes = filesize - start_bytes
        else:
            end_bytes = filesize // segment * (i+1)
        for tup in file_list:
            if tup[2] <= start_bytes and tup[3] >= end_bytes:
                t = threading.Thread(target=download_file_segment,
                                 args=(tup[0], tup[1], filename, i, start_bytes, end_bytes))
                t.run()
                break

    if filename == "":
        return

    folder_name = "./temp_client/" + hashlib.sha224(filename.encode()).hexdigest() + "/"
    filelist = os.listdir(folder_name)
    with open(filename, 'wb') as f:
        print('Writing to %s' % filename)
        for name in filelist:
            name = folder_name + name
            file_input = open(name, 'rb')
            f.write(file_input.read())
            file_input.close()
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
