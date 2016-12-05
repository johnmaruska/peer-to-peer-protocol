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

THIS_HOST = 'localhost'  # this system hostname
ps_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ps_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#self.welcome.bind((self.host, self.port))
ps_s.bind((THIS_HOST, 0))
THIS_PORT = ps_s.getsockname()[1]
cmd_q = queue.Queue()
LAST_UP = time.time()
UP_INTERVAL = 0;

class PeerServer:
    def __init__(self, welcome: socket.socket):
        self.welcome = ps_s
               

    def listen_to_client(self, client, address):
        try:
            filename = recv_from(client).lstrip('REQUEST ')
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
                threading.Thread(target=self.listen_to_client, args=(client,address)).start()
            except Exception as e:
                pass

    def quit(self):
        # TODO: Remove files from temporary folder.
        # TODO: Close all connected sockets
        self.welcome.close()


def main():
    import configparser
    confi = configparser.ConfigParser()
    confi.read('clientThreadConfig.cfg')
    sect = confi['Section']
    ts_port = int(sect['Port'])
    host_ip = sect['Ip']
    UP_INTERVAL = sect['Interval']

    ts_host = 'localhost'
    #ts_port = 60000
    cmd_q = queue.Queue()
    ps = PeerServer(ps_s)
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
    finally:
        # TODO: Check and see if killing threads or otherwise stopping them 
        # is a possibility and required here.
        ps.quit()


def commands(cmd_q):
    try:  # loop input and enqueue command
        while True:
            time.sleep(0.1)
            cmd = input('$ ')
            if time.time()-LAST_UP < UP_INTERVAL*60:
                flist.open('filelist.txt', 'r')
                size = os.path.getsize(filename)
                for line in flist:
                    cmd_q.put("updatetracker %s 0 %s %s %s" % (filename, size, THIS_HOST, THIS_PORT))
                flist.close()

            try:
                cmd_args = re.match('^([^ ]+) (.*)', cmd)
                accepted_commands = ['createtracker', 'updatetracker', 'GET']
                if cmd == 'REQ LIST' or cmd == 'LIST':
                    cmd_q.put('REQ LIST')
                elif cmd_args.group(1) in accepted_commands:
                    cmd_q.put(cmd)
            except AttributeError:
                print('Not a valid command.')
    except KeyboardInterrupt:
        pass


def hashfile(afile, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hashlib.md5().update(buf)
        buf = afile.read(blocksize)
    return hashlib.md5().hexdigest()


def createtracker(filename, desc):
    if os.path.isfile(filename):
        size = os.path.getsize(filename)
        md5 = hashfile(open(filename, 'rb'))
        ip = THIS_HOST
        port = THIS_PORT
        flist = open('filelist.txt', 'w')
        flist.write("%s /n" %filename)
        flist.close()
        return 'createtracker %s %s %s %s %s %s' % (filename, size, desc, md5, ip, port)
    else:
        return 'createtracker fail'


def cmd_tracker(server, cmd_q):
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
            flist.open('filelist.txt', 'r+')
            found = False
            for line in flist:
                if filename in line:
                    found = True
            if found:
                flist.write("%s /n" %filename)
            flist.close()

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
    return filelist


def download_file(host: str, port: int, original_filename, original_checksum):
    # TODO: call GET, parse results, assign IP and port
    print('Downloading file.')
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    encode_and_send(server, ('REQUEST %s' % original_filename))
    print("REQUEST %s" % original_filename)
    if not os.path.exists("./temp_client/"):
        os.mkdir("./temp_client/")
    else:
        clearfile = os.listdir("./temp_client/")
        print(clearfile)
        for s in clearfile:
            os.remove("./temp_client/" + s)
    segment_name = recv_from(server)
    segment_length = int(segment_name.split(' ')[1])
    nth_segment = random.randint(0, segment_length-1)
    count = 0
    while count < segment_length:
        print('Segment count: %s' % count)
        filename = 'temp_client/output' + str(nth_segment)
        with open(filename, 'wb') as output:
            print('Writing to %s' % filename)
            command = 'REQUEST %s' % str(nth_segment)
            encode_and_send(server, command)
            received = recv_from(server)
            filesize = int(received)
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
            # TODO: Tell tracking server to updatetracker with start/end
    encode_and_send(server, 'FINISH')
    os.chdir('./temp_client/')
    filelist = os.listdir('.')
    with open(original_filename, 'wb') as f:
        print('Writing to %s' % original_filename)
        for name in filelist:
            file_input = open(name, 'rb')
            f.write(file_input.read())
            file_input.close()
            
    # TODO: Checksum comparison of file. Not sure what we do in event of a fail.
    new_checksum = hashfile(original_filename)
    if new_checksum == original_checksum:
        # Checksum passes - file uncorrupted
        pass
    else:
        # checksum does not pass - file corrupted
        pass
    

def track_comm(host: str, port: int, cmd_q: queue.Queue):
    while True:
        try:
            if not cmd_q.empty():
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.connect((host, port))
                cmd_tracker(server, cmd_q)
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
    if server_response[0] == 'REP GET BEGIN':
        for line in server_response:
            if 'Filename: ' in line:
                filename = line.lstrip('Filename: ')
            if 'MD5: ' in line:
                checksum = line.lstrip('MD5: ')
            # (ip_addr:port_num:start_byte:end_byte:time
            m = re.match('([^:]+):([^:]+):([^:]+):([^:]+):([^:]+)', line)
            if m:
                ip_addr = m.group(1)
                port_num = int(m.group(2))
                print('Match found: %s %s' % (ip_addr, port_num))
                download_file(ip_addr, port_num, filename, checksum)
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
