"""
    Peer Program for P2P File Transfer Protocol
    Handles both client and server portions of peer terminal.
"""

import hashlib
import math
import os
import random
import re
import socket
import sys
import threading
import time
import queue
import configparser


THIS_HOST = "localhost"
cmd_q = queue.Queue()
kill_all_threads = False
ps_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ps_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ps_s.bind((THIS_HOST, 0))
THIS_PORT = ps_s.getsockname()[1]

confi = configparser.ConfigParser()
confi.read('clientThreadConfig.cfg')
sect = confi['Section']
TS_PORT = int(sect['Port'])
HOST_IP = sect['Ip']
UP_INTERVAL = int(sect['Interval'])
MAX_CHUNK_SIZE = int(sect['Filesize'])
TS_HOST = 'localhost'

class PeerServer:
    def __init__(self, welcome: socket.socket):
       self.welcome = ps_s

    @staticmethod
    def listen_to_client(client, address):
        global kill_all_threads
        try:
            filename = recv_from(client)
            filename = filename[8:]
            print(filename)
            foldername = 'temp_client/' + hashlib.sha224(filename.encode()).hexdigest() + '/'
            segment_number = len(os.listdir('./' + foldername + '/'))
            msg = "SEGMENT " + str(segment_number)
            encode_and_send(client, msg)
            while not kill_all_threads:
                # TODO: receive messages and send data
                res = recv_from(client)
                print(res)
                if res == "FINISH":
                    break
                if res.split(' ')[0] == "REQUEST":
                    res_list = res.split(' ')
                    filename = 'temp' + res_list[1]
                    os.chdir(foldername)
                    file_size = os.path.getsize(filename)
                    file_size = str(file_size)
                    encode_and_send(client, file_size)
                    output = open(filename, "rb")
                    l = output.read(4096)
                    while l:
                        client.send(l)
                        l = output.read(4096)
                    os.chdir('../')
                    os.chdir('../')
                    output.close()
        except ConnectionResetError:
            print("ConnectionResetError: Connection forcibly closed by remote host.")
        except (TypeError, OSError) as e:
            print("%s: Non-existent file requested." % e)
        except Exception as e:
            print("Unexpected exception: %s" % e)
            raise e
        finally:
            client.close()

    def listen(self):
        global kill_all_threads
        self.welcome.listen(20) # from 5 to 20
        while not kill_all_threads:
            try:
                (client, address) = self.welcome.accept()
                # creates a new thread for each client that joins in
                threading.Thread(target=self.listen_to_client, args=(client, address)).start()
            except Exception:
                pass

    def quit(self):
        # TODO: Remove files from temporary folder.
        # TODO: Close all connected sockets
        self.welcome.close()


def main():
    ps = PeerServer(ps_s)
    try:  # Program will conclude when communication to the tracking server is cut.
        # Peer functions as a server for other peer-clients
        ps_t = threading.Thread(target=ps.listen)
        # one thread for connection to the server
        ts_t = threading.Thread(name='track', target=track_comm, args=(TS_HOST, TS_PORT))
        # one thread for raw input
        in_t = threading.Thread(name='input', target=commands, args=())
        in_t.setDaemon(True)
        # Start all threads.
        ts_t.start()
        ps_t.start()
        in_t.start()
        while ps_t.is_alive() and ts_t.is_alive() and in_t.is_alive():
            pass
    except RuntimeError:
        print("ERROR: Could not start all threads.")
    finally:
        # TODO: Check and see if killing threads or otherwise stopping them
        # is a possibility and required here.
        ps.quit()

def timeup():
    threading.Timer(UP_INTERVAL, timeup).start()
    flist=open('filelist.txt', 'r')
    for line in flist:
        if not line.isspace():
            size = os.path.getsize(line)
            cmd_q.put("updatetracker %s 0 %s %s %s" % (line, size, THIS_HOST, THIS_PORT))
    flist.close()
timeup()

def commands():
    global kill_all_threads
    while not kill_all_threads:
        time.sleep(0.1)
        cmd = input('$ ')
        try:
            cmd_args = re.match('^([^ ]+) (.*)', cmd)
            accepted_commands = ['createtracker', 'updatetracker', 'GET']
            if cmd == 'LIST' or cmd == 'REQ LIST':
                cmd_q.put('REQ LIST')
            elif cmd == 'quit()':
                kill_all_threads = True
            elif cmd_args.group(1) in accepted_commands:
                cmd_q.put(cmd)
        except AttributeError:
            print('Not a valid command.')


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
        flist = open('filelist.txt', 'w')
        flist.write("%s"  %filename)
        flist.close()
        return 'createtracker %s %s %s %s %s %s' % (filename, size, desc, md5, ip, port)
    else:
        return 'createtracker fail'


def cmd_tracker(server):
    msg = ""
    next_cmd = cmd_q.get()
    if re.match('createtracker .*', next_cmd):
        # createtracker filename description
        m = re.match('(createtracker) ([^ ]+) (".*")', next_cmd)
        try:
            filename = m.group(2)
            desc = m.group(3)
            msg = createtracker(filename, desc)
            if os.path.isfile(filename):
                # Long process time. Split into thread for more rapid server response.
                threading.Thread(target=split_file, args=(filename,)).start()
            else:
                print("Cannot create tracker. This file does not exist.")
                return
        except AttributeError:
            print('Improper number of arguments. createtracker is formatted as: createtracker [filename] "[description]"')
            return
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
            flist=open('filelist.txt', 'r+')
            found = False
            for line in flist:
                if filename in line:
                    found = True
            if not found:
                flist.write("%s" %filename)
            flist.close()
        except AttributeError:
            print('Improper number of arguments. Argument is formatted as: '
                  'updatetracker [filename] [start_bytes] [end_bytes] [ip-address] '
                  '[port-number]')
            return

    elif re.match('GET .*', next_cmd):
        msg = next_cmd

    elif next_cmd == 'REQ LIST':
        msg = "REQ LIST\n"

    msg += ";endTCPmessage"

    if len(msg) > 14:
        encode_and_send(server, msg)
        recv_from_tracker(server)


def split_file(filename):
    global MAX_CHUNK_SIZE
    try:
        size = os.path.getsize(filename)
    except FileNotFoundError:  # Sometimes randomly doesn't find the file - try again.
        try:
            size = os.path.getsize(filename)
        except FileNotFoundError:
            print("FileNotFoundError: The system cannot find the file specified: %s" % filename)
            return
    number_of_file = math.ceil(float(size) / MAX_CHUNK_SIZE)
 #   if not os.path.isdir('./temp_client/'):
 #       os.mkdir('./temp_client/')
    # Create hash folder to store split file segments
    folder_name = 'temp_client/' + hashlib.sha224(filename.encode()).hexdigest()
    if not os.path.exists("./" + folder_name): 
        os.makedirs(folder_name)

    # Actually split the file into the separate segments
    with open(filename, "rb") as f:
        n = size // number_of_file
        os.chdir(folder_name)
        for i in range(0, number_of_file):
            if i == number_of_file - 1:
                readsize = size - (number_of_file - 1) * n
            else:
                readsize = n
            in_file = open("temp" + str(i), "wb")
            in_file.write(f.read(readsize))
            in_file.close()

    filelist = os.listdir('.')
    for i in range(0, len(filelist)):  # prepend the name of the folder to each file name
        filelist[i] = "./" + folder_name + "/" + filelist[i]
    os.chdir("../")  # scope back into the proper working directory
    os.chdir("../")

    return filelist



def download_file_segment(host: str, port: int, original_filename: str, segment: int):
    print('Downloading file.')
    peer_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_server.connect((host, port))
    encode_and_send(peer_server, ('REQUEST %s' % original_filename))  # TODO: Needs second argument: segment
    print("REQUEST %s" % original_filename)

    # Make sure there's a proper storage folder for the file segments.
    folder_name = "./temp_client/" + hashlib.sha224(original_filename.encode()).hexdigest() + "/"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    segment_name = recv_from(peer_server)
    nth_segment = segment
    # Download file part
    filename = folder_name + 'temp' + str(nth_segment)
    with open(filename, 'wb') as output:
        print('Writing to %s' % filename)
        command = 'REQUEST %s' % str(nth_segment)
        encode_and_send(peer_server, command)
        received = recv_from(peer_server)
        filesize = int(received)
        total = 0
        while True:
            if total >= filesize:
                break
            received = peer_server.recv(4096)
            output.write(received)
            total += len(received)

    encode_and_send(peer_server, 'FINISH')
    peer_server.close()
    return filesize


def track_comm(host: str, port: int):
    global kill_all_threads
    while not kill_all_threads:
        try:
            if not cmd_q.empty():
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.connect((host, port))
                cmd_tracker(server)
                server.close()
        except ConnectionRefusedError:
            print("ConnectionRefusedError: Tracking server currently down. Try again later.")
            break


def track_file_ext(f_name: str):
    if re.match('.*\.[\w]+\Z', f_name):
        if not re.match('.*\.track\Z', f_name):
            f_track = re.sub('\.[\w]+\Z', '.track', f_name)
        else:  # file already has .track extension
            f_track = f_name
    else:  # appends .track if no given file extension
        f_track = f_name + ".track"
    return f_track


def write_local_tracker(reply: list, f_name: str, checksum: str):
    # Remove server reply wrappers
    reply.remove('REP GET BEGIN')
    reply.remove('REP GET END ' + checksum)
    # Give a .track extension
    f_track = './temp_client/' + track_file_ext(f_name)
    # Make sure there's a ./temp_client/ folder to use.
    if not os.path.exists('./temp_client/'):
        os.makedirs('./temp_client/')
    # Write local
    with open(f_track, 'wt') as f:
        f.write('\n'.join(reply))


def remove_local_tracker(f_name: str):
    f_track = './temp_client/' + track_file_ext(f_name)
    try:
        os.remove(f_track)
    except FileNotFoundError:
        pass


def download_manager(f_name: str, f_size: int, peers: list, checksum: str):
    global kill_all_threads
    global MAX_CHUNK_SIZE
    if f_name == "":
        return
    # Peer list parameters:
    #   [(ip_addr, port_num, start_byte, end_byte, time),...]
    seg_total = math.ceil(float(f_size) / MAX_CHUNK_SIZE)
    try:
        foldername = './temp_client/' + hashlib.sha224(f_name.encode()).hexdigest() + '/'
        filelist = os.listdir(foldername)
        filelist = [int(x.lstrip('temp')) for x in filelist]
        last_segment = max(filelist)
        last_byte = MAX_CHUNK_SIZE * last_segment + os.path.getsize(foldername + 'temp' + str(last_segment))
    except (FileNotFoundError, TypeError, ValueError) as e:
        last_segment = 0
        last_byte = 0

    # Try and download all chunks.
    for i in range(last_segment, seg_total):
        if kill_all_threads:
            return False
        # check for peers with needed code block
        potential_seeds = []
        downloaded = False
        for peer in peers:
            # Check if has bytes needed and is not self.
            if peer[3] > last_byte and not (peer[0] == THIS_HOST and peer[1] == THIS_PORT):
                potential_seeds.append(peer)
        # Sort by descending timestamp. Most recent first.
        sorted_seeds = sorted(potential_seeds, key=lambda x: x[3], reverse=True)
        for peer in sorted_seeds:
            try:  # download_file_segment will throw an exception if it fails.
                last_byte += download_file_segment(peer[0], peer[1], f_name, i)
                msg = "updatetracker %s %s %s %s %s\n" % (f_name, 0, last_byte, THIS_HOST, THIS_PORT)
                cmd_q.put(msg)
                downloaded = True
                break
            except Exception as e:  # if the download fails remove the peer from seeds
                print("ERR: ", e)
                sorted_seeds.remove(peer)
        if not downloaded and not sorted_seeds:  # Halt the download manager if no available peers
            print("Not downloaded and sorted empty.")
            return
    merge_segments(f_name)
    remove_local_tracker(f_name)
    new_checksum = hashfile(f_name)
    flist = open('filelist.txt', 'w')
    flist.write("%s" %f_name)
    flist.close()
    if new_checksum != checksum:
        print("ERROR: File was corrupted.")
        os.remove(f_name)  # Remove corrupted file
        remove_segment_folder(f_name)
        cmd_q.put('updatetracker %s %s %s %s %s' % (f_name, 0, 0, THIS_HOST, THIS_PORT))
        print("Corrupted content deleted - please try again.")
        return False
    return True


def remove_segment_folder(f_name: str):
    print("Removing folder of corrupted segments")
    folder_name = "./temp_client/" + hashlib.sha224(f_name.encode()).hexdigest() + "/"
    filelist = os.listdir(folder_name)
    [os.remove(folder_name + x) for x in filelist]
    os.rmdir(folder_name)


# Merge segments back into a single file.
def merge_segments(f_name: str):
    folder_name = "./temp_client/" + hashlib.sha224(f_name.encode()).hexdigest() + "/"
    filelist = os.listdir(folder_name)
    with open(f_name, 'wb') as f:
        print('Writing to %s' % f_name)
        for name in filelist:
            name = folder_name + name
            file_input = open(name, 'rb')
            f.write(file_input.read())
            file_input.close()


def recv_from_tracker(server: socket.socket):
    response = recv_from(server)
    print(response)
    response = response.split('\n')
    peer_list = []
    filesize = 0
    filename = ""
    if response[0] == 'REP GET BEGIN':
        # Parse for download information.
        for line in response:
            if 'Filename: ' in line:
                filename = line[10:]  # TODO: the number is weird.
                print("IN IF FILENAME: ", filename)
            if 'Filesize: ' in line:
                filesize = int(line[10:])
            if 'MD5: ' in line:
                md5 = line[5:]
            # ip_addr:port_num:start_byte:end_byte:time
            m = re.match('([^:]+):([^:]+):([^:]+):([^:]+):([^:]+)', line)
            if m:
                file_tuple = (m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5))
                peer_list.append(file_tuple)

        write_local_tracker(response, filename, md5)
        dm_t = threading.Thread(target=download_manager, args=(filename, filesize, peer_list, md5))
        dm_t.start()


def recv_from(server: socket.socket):
    end_marker = ";endTCPmessage"
    total_msg = []
    timeout = time.time() + 30 # 30 second timeout
    while time.time() < timeout:
        
        try:
            msg = (server.recv(1024)).decode("utf-8")
        except ConnectionAbortedError as e:
            return e
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
