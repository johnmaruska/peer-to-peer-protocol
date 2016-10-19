import os, sys
import socket
import subprocess
#Rewrite the whole socketserver

def split_file(filename, number_of_file):
    '''
    #For macOS, it doesn't have command for split -n, use split -b instead for testing
    command = "split -n"
    number_of_file = 3
    command += " " + str(number_of_file)
    suffix = "./temp/"
    command += " " + filename + " " + suffix
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    filelist = os.listdir('./temp')
    os.chdir("./temp")
    #p = subprocess.Popen("cat * >> input.pdf", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #print (file)
    return filelist
    '''
    #Make split function irrelevant to OS
    size = os.path.getsize(filename)
    with open(filename, "rb") as f:
        n = size // number_of_file
        os.chdir("./temp/")
        for i in range(0, number_of_file):
            if i == 2:
                readsize = size - (number_of_file-1) * n
            else:
                readsize = n
            input = open("input" + str(i), "wb")
            input.write(f.read(readsize))
            input.close()
    filelist = os.listdir('.')
    return filelist

def handle(sock):
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
    filename = "a.jpg"
    filelist = split_file(filename, 10)
    sock.send(filename.encode())
    print("split files")
    segment_number = len(filelist)
    print (segment_number)
    msg = "SEGMENT " + str(segment_number)
    sock.send(msg.encode())

    nth_segment = 0
    # split the file & Send
    while True:
        res = ""
        res = sock.recv(1024)
        print(res)
        res = res.decode('utf-8')
        if res == "FINISH":
            break
        if res.split(' ')[0] == "REQUEST":
            res_list = res.split(' ')
            print (int(res_list[1]))
            print ("Send File" + res_list[1])
            #FILE SIZE
            file_size = os.path.getsize(filelist[int(res_list[1])])
            file_size = str(file_size)
            sock.send(file_size.encode())
            output = open(filelist[int(res_list[1])], "rb")
            l = output.read(4096)
            while(l):
                sock.send(l)
                l = output.read(4096)
            output.close()
        if res == "DONE":
            continue

if __name__ == "__main__":
    HOST, PORT = "localhost", 31024

    # Create the server, binding to localhost on port 9999
    server = socket.socket()
    server.bind((HOST, PORT))
    server.listen(10)
    client ,addr = server.accept()
    print("Got a connection from %s" % str(addr))
    handle(client)



