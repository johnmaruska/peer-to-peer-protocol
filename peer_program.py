'''
    Peer Program for P2P File Transfer Protocol
    Handles both client and server portions of peer terminal.
'''

import socket
import threading
import queue

class PeerServer():
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        # TODO: wrap these in try blocks ?
        self.welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.welcome.setsockopt(SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.welcome.bind((self.host, self.port))
    
    def listen(self):
        self.welcome.listen(10) # 5 maximum clients connected to each Peer.
        while True:
            client, address = self.welcome.accept()
            # creates a new thread for each client that joins in
            threading.Thread(target=listenToClient, args=(client,address)).start()
            
    def quit(self):
        self.welcome.close()
            
    def listenToClient(self, client, address):
        try:
            while True:
                # TODO: receive messages and send data
                # P2P Protocol goes here.
                
        except KeyboardInterrupt:
            client.close()
            
    # TODO: implement send file as a server. Use code from GitHub.
    def send_file():
        pass

def main():
    this_host = 'localhost' # this system hostname
    this_port = 8888 # this system port number
    ts_host = ''
    ts_port = 9999
    cmd_q = queue.Queue()
    ps = PeerServer(this_host, this_port)
    
    # Peer functions as a server for other peer-clients    
    ps_t = threading.Thread(target=ps.listen).start()
    # one thread for connection to the server
    ts_t = threading.Thread(name='track', target=track_comm, args=(ts_host, ts_port, cmd_q)).start()
    # one thread for raw input
    in_t = threading.Thread(name='input', target=commands, args=(cmd_q)).start()
        
    while(ps_t.is_alive() && ts_t.is_alive() && in_t.is_alive()):
        pass
            
def commands(cmd_q: Queue):
    try: # loop input and enqueue command
        while(True):
            cmd = input('$ ')
            cmd_args = cmd.split(' ')
            
            if(cmd_args[0] == 'createtracker'):
                if(len(cmd_args) == 7):
                    cmd_q.put(cmd_args)
                else:
                    print("Improper number of arguments. Argument is formatted as: \
                           createtracker [filename] [filesize] [description] [md5] \
                           [ip-address] [port-number]")
            elif(command_args[0] == 'updatetracker'):
                if(len(cmd_args) == 6):
                    cmd_q.put(cmd_args)
                else:
                    print("Improper number of arguments. Argument is formatted as: \
                           updatetracker [filename] [start_bytes] [end_bytes] \
                           [ip-address] [port-number]")
            elif(command_args[0] == 'GET'):
                if(len(cmd_args) == 2):
                    cmd_q.put(cmd_args)
                else:
                    print("Improper number of arguments. Argument is formatted as: \
                           GET [filename]")
            elif(command_args[0] == 'REQ' and command_args[1] == 'LIST'):
                if(len(cmd_args) == 2):
                    cmd_q.put(cmd_args)
                else:
                    print("Improper number of arguments. REQ LIST has no arguments.")
    except KeyboardInterrupt:
        pass


def cmd_tracker(server: socket.socket, cmd_q: Queue):
    msg = ""
    next_cmd = cmd_q.get()
    
    if(next_cmd[0]=='createtracker'):
        filename = next_cmd[1]
        filesize = next_cmd[2]
        desc = next_cmd[3]
        md5 = next_cmd[4]
        ip_addr = next_cmd[5]
        port_num = next_cmd[6]   
        msg = "createtracker %s %s %s %s %s %s" % (filename, filesize, desc, md5, 
                                                    ip_addr, port_num) 
    elif(next_cmd[0]=='updatetracker'):
        filename = next_cmd[1]
        start_bytes = next_cmd[2]
        end_bytes = next_cmd[3]
        ip_addr = next_cmd[4]
        port_num = next_cmd[5]
        msg = "updatetracker %s %s %s %s %s" % (filename, start_bytes, end_bytes,
                                                ip_addr, port_num)
    elif(next_cmd[0]=='GET'):
        filename = next_cmd[1]
        msg = "GET %s" % filename
    elif(next_cmd[0]=='REQ' and next_cmd[1]=='LIST'):
        msg = "REQ LIST"
    
    if(len(msg) > 0):
        server.sendall(msg)  
        
        
def track_comm(host: str, port: int, cmd_q: Queue):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((host, port))
    try:
        while(True):
            cmd_tracker(server, cmd_q)
            recv_from_tracker(server)
          
    except KeyboardInterrupt:
        server.close()

# TODO: receive from tracker. Need to figure out how to 
def recv_from_tracker(server: socket.socket):
    pass
            
# TODO: Need to implement actual download_file protocol. Take from GitHub.
        
if __name__=="__main__":
    sys.exit(main())