import os
import socket
import subprocess


#Rewrite the whole socketserver

def split_file(self, filename, number_of_file):
    #For macOS, it doesn't have command for split -n, use split -b instead for testing
    command = "split -b"
    number_of_file = 10**6
    command += " " + str(number_of_file)
    filename = "input.pdf"
    suffix = "./temp/"
    command += " " + filename + " " + suffix
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    filelist = os.listdir('./temp')
    os.chdir("./temp")
    #p = subprocess.Popen("cat * >> input.pdf", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #print (file)
    return filelist

def handle(self):
    # self.request is the TCP socket connected to the client
    # Send file when client connects
    '''
    Server send the segment length at very first.
        SEGMENT [numbers of segment]
    Client should ask the segment first, or return the segment number it received last time.
    And the format should be:
        SUCCESS [number]
        REQUEST [number]
        FINISH

    '''
    # split file
    print("split files")
    filelist = self.split_file("input.pdf", 10)
    segment_number = len(filelist)
    msg = "SEGMENT " + str(segment_number)
    self.request.sendall(msg)
    res = ""
    res = self.request.recv(1024)
    print res
    nth_segment = 0
    # split the file & Send
    while True:
        if res == "FINISH":
            break
        if res.split(' ')[0] == "REQUEST":
            print res
            res_list = res.split(' ')
            print (int(res_list[1]))
            print ("Send File" + res_list[1])
            output = open(filelist[int(res_list[1])], "rb")
            self.request.send(output.read())
            res = self.request.recv(1024)
            print (res)
            output.close()



if __name__ == "__main__":
    HOST, PORT = "localhost", 30000

    # Create the server, binding to localhost on port 9999
    server = socket.socket()
    server.connect((HOST, PORT))
    server.listen(10)
    clientsocket,addr = server.accept()
    print("Got a connection from %s" % str(addr))


