'''
    Tracking Server Program for P2P File Transfer Protocol
'''

import glob
import os
import queue
import re
import socket
import threading
import time

# TODO: Fix message structure to include '<' '>' '\n' characters.

def main():
    host = ''
    port = 9999
    welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    welcome.setsockopt(SOL_SOCKET, socket.SO_REUSEADDR, 1)
    welcome.bind((host, port))
    
def listen(welcome: socket.socket):
    welcome.listen(5) # 10 maximum clients connected to server.
    try:
        # create a thread for each peer client that wants to interact with server
        while True:
            client, address = welcome.accept()
            threading.Thread(target=listenToClient, args=(client,address)).start()
    finally
        welcome.close()

def listenToClient(client, address):
    try:
        while True:
            # receive command
            cmd_in = recv_msg(client)
            
            # Check for and execute createtracker command
            if re.match("createtracker *", cmd_in):
                try:
                    # grab the arguments of the createtracker command.
                    # ("*") allows description to contain spaces; others space limited
                    m = re.match('(createtracker) ([^ ]+) ([^ ]+) ("*") ([^ ]+) ([^ ]+)'
                                 ' ([^ ]+)', cmd_in)
                    f_name = m.group(2); f_size = m.group(3)
                    desc = m.group(4); md5 = m.group(5)
                    ip_addr = m.group(6); port_num = m.group(7)
                    reply_out = createtracker(f_name, f_size, desc, md5, ip_addr, port_num)
                    client.send(reply_out)
                except IndexError, AttributeError: 
                    reply_out = '<createtracker fail>\n'
                    client.send(reply_out)
            
            # Check for and execute updatetracker command
            elif re.match('updatetracker *', cmd_in):
                try:
                    m = re.match('(updatetracker) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+)')
                    f_name = m.group(2)
                    start_bytes = m.group(3); end_bytes = m.group(4)
                    ip_addr = m.group(5); port_num = m.group(6)
                    reply_out = updatetracker(f_name, start_bytes, end_bytes, ip_addr, port_num)
                    client.send(reply_out)
                except IndexError, AttributeError:
                    reply_out = '<updatetracker fail>\n'
                    client.send(reply_out)           
            
            # Check for and execute REQ LIST command
            elif cmd_in == "REQ LIST":
                reply_out = req_list()
                client.send(reply_out)
            
            # Check for and execute GET command
            elif cmd_in == "GET *", cmd_in):
                m = re.match("GET ([^ ]+\.track)")
                try:
                    tracker_file = m.group(1)
                    reply_out = get(tracker_file)
                except AttributeError:
                    reply_out = cmd_in + ' does not request a .track file.'

    except KeyboardInterrupt:
        client.close()
            
def get(tracker): -> str
    reply = '<REP GET BEGIN>\n<'
    with open(tracker, 'r') as f:
        for line in f:
            reply.append(line)
            if "MD5: " in line:
                md5 = line.split(' ')[1]
    reply.append('>\nREP GET END %s>\n' % md5)
    return reply
            
def req_list(): -> str
    # os.chdir("/mydir") #mydir would have to be changed
    track_files = glob.glob('./*.track')
    reply_msg = '<REP LIST %s>\n' % len(track_files)
    for file in range(len(track_files)):
        # read file
        with open(track_files[file], 'r') as f:
            for line in f:
                if "Filename: " in line:
                    name = line.split(' ')[1]
                elif "Filesize: " in line:
                    size = line.split(' ')[1]
                elif "MD5: " in line:
                    md5 = line.split(' ')[1]
        reply_msg.append('<%s %s %s %s>\n' %(f, name, size, md5))
    reply_msg.append('<REP LIST END>\n')
    return reply_msg
        
def updatetracker(f_name, start_byte, end_byte, ip_addr, port_num): -> str
    '''
        Does the bulk of the updatetracker command. i.e. modifying the tracker file.
        Returns the reply string to send back to the client.
    '''
    # Ensure the file name ends with '.track' extension.
    if re.match('\.[\w]+\Z',f_name):
        if not re.match('\.track\Z', f_name):
            f_track = re.sub('\.[\w]+\Z', '.track', f_name)
        else:
            f_track = f_name
    else
        f_track = f_track + ".track"
    # Modify and rewrite file with new information.
    if os.path.isfile('./%s' % f_track):
        try:
            with open(f_track, 'r') as f:
                prev_contents = f.read()
            old_pattern = '%s:%s:[^:]+:[^:]:[\w]+' % (ip_addr, port_num)
            timestamp = time.time()
            new_line = '%s:%s:%s:%s:%s' % (ip_addr, port_num, start_byte, end_byte, timestamp)
            new_contents = re.sub(pattern, new_line, prev_contents)
            with open(f_track, 'w') as f
                f.write(new_contents)
            reply_out = '<updatetracker succ>\n'
        except:
            reply_out = '<updatetracker fail>\n'
    else:
        reply_out = '<updatetracker ferr>\n'
    
    return reply_out
        
def createtracker(f_name, f_size, desc, md5, ip_addr, port_num): -> str
    ''' 
        Does the bulk of the createtracker command, i.e. create the tracker file 
        Filename cannot contain any '.' characters that don't prefix the file extension.
        Returns the reply string to send back to the client.
    '''
    if os.path.isfile('./%s' % f_name):
        # File already exists
        reply_out = '<createtracker ferr>\n'
    else
        # Changes file extension to .track
        if re.match('\.[\w]+\Z'):
            if not re.match('\.track\Z', f_name):
                f_track = re.sub('\.[\w]+\Z', '.track', f_name)
            else: # file already has .track extension
                f_track = f_name
        else # appends .track if no given file extension
            f_track = f_track + ".track"
        with open(f_track, 'w') as f
            f.write('Filename: %s\n' % f_track)
            f.write('Filesize: %s\n' % f_size)
            f.write('Description: %s\n' % desc)
            f.write('MD5: %s\n' % md5)
            f.write('# all comments must begin with # and must be ignored by the file parser\n'
                    '# following the above fields about file to be shared will be list of peers'
                    'sharing this file\n')
            timestamp = time.time()
            f.write('%s:%s:0:%s:%s' % (ip_addr, port_num, file_size,timestamp)
        reply_out = '<createtracker succ>\n'
    return reply_out
    
def recv_msg(client: socket.socket): -> str
    end_marker = ";endTCPmessage"
    total_msg=[]
    msg=''
    while True:
        msg = client.recv(1024)
        if end_marker in msg:
            total_msg.append(msg[:msg.find(end_marker)])
            break
        total_msg.append(msg)
        if len(total_msg) > 1:
            # check if end of msg was split
            last_pair = total_msg[-2]+total_msg[-1]
            if end_marker in last_pair:
                total_msg[-2] = last_pair[:last_pair.find(end_marker)]
                total_msg.pop()
                break
    return ''.join(total_msg)