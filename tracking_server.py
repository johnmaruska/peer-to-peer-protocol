"""
    Tracking Server Program for P2P File Transfer Protocol
"""

import glob
import os
import re
import socket
import sys
import threading
import time


# TODO: Fix message structure to include '<' '>' '\n' characters.
def main():
    host = 'localhost'
    port = 9999
    welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    welcome.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    welcome.bind((host, port))
    listen(welcome)


def listen(welcome: socket.socket):
    welcome.listen(5)  # 5 maximum clients connected to server.
    try:
        # create a thread for each peer client that wants to interact with server
        while True:
            client, address = welcome.accept()
            threading.Thread(target=listen_to_client, args=(client,)).start()
    finally:
        welcome.close()


def listen_to_client(client):
    try:
        while True:
            # receive command
            cmd_in = recv_msg(client)
            # Check for and execute createtracker command
            if re.match("createtracker .*", cmd_in):
                try:
                    # grab the arguments of the createtracker command.
                    # ("*") allows description to contain spaces; others space limited
                    m = re.match('(createtracker) ([^ ]+) ([^ ]+) (".*") ([^ ]+) ([^ ]+)'
                                 ' ([^ ]+)', cmd_in)
                    f_name = m.group(2)
                    f_size = m.group(3)
                    desc = m.group(4)
                    md5 = m.group(5)
                    ip_addr = m.group(6)
                    port_num = m.group(7).strip('\n')
                    reply_out = createtracker(f_name, f_size, desc, md5, ip_addr, port_num)
                    reply_out += ';endTCPmessage'
                    client.send(reply_out.encode('utf-8'))
                except (IndexError, AttributeError):
                    reply_out = 'createtracker fail\n'
                    client.send(reply_out.encode('utf-8'))
            # Check for and execute updatetracker command
            if re.match('updatetracker .*', cmd_in):
                try:
                    m = re.match('(updatetracker) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+)', cmd_in)
                    f_name = m.group(2)
                    start_bytes = m.group(3)
                    end_bytes = m.group(4)
                    ip_addr = m.group(5)
                    port_num = m.group(6).strip('\n')
                    reply_out = updatetracker(f_name, start_bytes, end_bytes, ip_addr, port_num)
                    reply_out += ";endTCPmessage"
                    client.send(reply_out.encode('utf-8'))
                except (IndexError, AttributeError):
                    reply_out = 'updatetracker fail\n'
                    client.send(reply_out.encode('utf-8'))
            # Check for and execute REQ LIST command
            if cmd_in == 'REQ LIST\n':
                reply_out = req_list()
                client.send(reply_out.encode('utf-8'))
            # Check for and execute GET command
            if re.match('GET .*\\n$', cmd_in):
                m = re.match('GET ([^ ]+\.track)', cmd_in)
                try:
                    tracker_file = m.group(1)
                    reply_out = get(tracker_file)
                except AttributeError:
                    reply_out = cmd_in.strip('\n') + ' does not request a .track file.'
                reply_out += ';endTCPmessage'
                client.send(reply_out.encode('utf-8'))

    except KeyboardInterrupt:
        client.close()


def get(tracker):
    reply = 'REP GET BEGIN\n'
    md5 = ''
    try:
        with open(tracker, 'rt') as f:
            for line in f:
                reply += line
                if "MD5: " in line:
                    md5 = line.split(' ')[1]
        reply += '\nREP GET END'
        if md5 != '':
            reply += (' %s\n' % md5)
    except FileNotFoundError:
        reply = 'ERROR: Could not GET. File %s not found.' % tracker
    return reply


def req_list():
    # os.chdir("/mydir") #mydir would have to be changed
    track_files = glob.glob('./*.track')
    reply_msg = 'REP LIST %s\n' % len(track_files)
    file_num = 0
    for t_file in range(len(track_files)):
        file_num += 1
        try:
            with open(track_files[t_file], 'rt') as f:
                for line in f:
                    if "Filename: " in line:
                        name = line.split(' ')[1].strip('\n')
                    elif "Filesize: " in line:
                        size = line.split(' ')[1].strip('\n')
                    elif "MD5: " in line:
                        md5 = line.split(' ')[1].strip('\n')

            reply_msg += ('%s %s %s %s\n' % (file_num, name, size, md5))
        except UnboundLocalError:
            reply_msg = '%s ERROR: %s not properly formatted.\n' % (file_num, track_files[t_file])
            pass
    reply_msg += 'REP LIST END\n;endTCPmessage'
    return reply_msg


def updatetracker(f_name, start_byte, end_byte, ip_addr, port_num):
    """
        Does the bulk of the updatetracker command. i.e. modifying the tracker file.
        Returns the reply string to send back to the client.
    """
    # Ensure the file name ends with '.track' extension.
    if re.match('[^ ]*\.[\w]+\Z', f_name):
        if not re.match('[^ ]+\.track\Z', f_name):
            f_track = re.sub("\.[\w]+\Z", '.track', f_name)
        else:
            f_track = f_name
    else:
        f_track = f_name + ".track"
    # Modify and rewrite file with new information.
    if os.path.isfile('./%s' % f_track):
        try:
            with open(f_track, 'rt') as f:
                old_pattern = '%s:%s:[^:]+:[^:]+:[\w]+' % (ip_addr, port_num)
                timestamp = int(round(time.time()))
                new_pattern = '%s:%s:%s:%s:%s' % (ip_addr, port_num, start_byte, end_byte, timestamp)
                new_contents = []
                for line in f:
                    if re.match(old_pattern, line):
                        new_line = re.sub(old_pattern, new_pattern, line)
                        print(new_line)
                        new_contents.append(new_line)
                    else:
                        print('Did not match new pattern')
                        new_contents.append(line)
            print(new_contents)
            with open(f_track, 'wt') as f:
                for line in new_contents:
                    f.write(line)

            reply_out = 'updatetracker succ\n'
        except FileNotFoundError:
            reply_out = 'updatetracker fail\n'
    else:
        reply_out = 'updatetracker ferr\n'

    return reply_out


def createtracker(f_name, f_size, desc, md5, ip_addr, port_num):
    """
        Does the bulk of the createtracker command, i.e. create the tracker file
        Filename cannot contain any '.' characters that don't prefix the file extension.
        Returns the reply string to send back to the client.
    """
    # Changes file extension to .track
    if re.match('.*\.[\w]+\Z', f_name):
        if not re.match('.*\.track\Z', f_name):
            f_track = re.sub('\.[\w]+\Z', '.track', f_name)
        else:  # file already has .track extension
            f_track = f_name
    else:  # appends .track if no given file extension
        f_track = f_name + ".track"

    if os.path.isfile('./%s' % f_track):
        # File already exists
        reply_out = 'createtracker ferr\n'
    else:
        with open(f_track, 'wt') as f:
            f.write('Filename: %s\n' % f_track)
            f.write('Filesize: %s\n' % f_size)
            f.write('Description: %s\n' % desc)
            f.write('MD5: %s\n' % md5)
            f.write('# all comments must begin with # and must be ignored by the file parser\n'
                    '# following the above fields about file to be shared will be list of peers '
                    'sharing this file\n')
            timestamp = time.time()
            f.write('%s:%s:0:%s:%s' % (ip_addr, port_num, f_size, timestamp))
        reply_out = 'createtracker succ\n'
    return reply_out


def recv_msg(client: socket.socket):
    end_marker = ";endTCPmessage"
    total_msg = []
    while True:
        try:
            msg = (client.recv(1024)).decode("utf-8")
            if end_marker in msg:
                total_msg.append(msg[:msg.find(end_marker)])
                break
        except TypeError:
            print(type(msg))
            print(type(end_marker))
            raise
        total_msg.append(msg)
        if len(total_msg) > 1:
            # check if end of msg was split
            last_pair = total_msg[-2] + total_msg[-1]
            if end_marker in last_pair:
                total_msg[-2] = last_pair[:last_pair.find(end_marker)]
                total_msg.pop()
                break
    return ''.join(total_msg)

if __name__ == "__main__":
    sys.exit(main())
