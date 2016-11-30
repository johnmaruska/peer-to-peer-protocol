from queue import Queue
import threading
import socket
import os
import random
   
class Downloader(threading.Thread):
    def __init__(self,  host, port, original_filename):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.original_filename = original_filename

    def run(self):
        self.download_file(self.host, self.port, self.original_filename)

    def download_file(self, host: str, port: int, original_filename): # (filename) # Shifted sendfile_client.py into this function.
        # TODO: call GET, parse results, assign IP and port
        print('Downloading file.')
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((host, port))
        self.encode_and_send(server, ('REQUEST %s' % original_filename))  # TODO: Needs second argument: segment
        print("REQUEST %s" % original_filename)
        # How does the server know to send this information?
        # file_name = server.recv(1024).decode('utf-8')
        if not os.path.exists("./temp_client"):
            os.mkdir("./temp_client/")
        else:
            clearfile = os.listdir("./temp_client/")
            print(clearfile)
            for s in clearfile:
                os.remove("./temp_client/" + s)
        segment_name = self.recv_from(server)
        segment_length = int(segment_name.split(' ')[1])
        nth_segment = random.randint(0, segment_length-1)
        count = 0
        while count < segment_length:
            print('Segment count: %s' % count)
            filename = 'temp_client/output' + str(nth_segment)
            with open(filename, 'wb') as output:
                print('Writing to %s' % filename)
                command = 'REQUEST %s' % str(nth_segment)
                self.encode_and_send(server, command)
                # received = server.recv(4096)
                received = self.recv_from(server)
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
        self.encode_and_send(server, 'FINISH')
        os.chdir('./temp_client/')
        filelist = os.listdir('.')
        with open(original_filename, 'wb') as f:
            print('Writing to %s' % original_filename)
            for name in filelist:
                file_input = open(name, 'rb')
                f.write(file_input.read())
                file_input.close()
        
    def recv_from(self, server: socket.socket):
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


    def encode_and_send(self, client: socket.socket, msg: str):
        msg += ';endTCPmessage'
        client.send(msg.encode('utf-8'))

if __name__ == "__main__":
    pass