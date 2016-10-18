import socket
import os, sys
import random
import subprocess
HOST, PORT = "localhost", 31024
# the second argument
data = " ".join(sys.argv[1:])
# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Connect to server and send data
sock.connect((HOST, PORT))
print ("connect!")
# Receive data from the server and shut down
count = 0
# Receive Filename
file_name = sock.recv(1024)
file_name = file_name.decode('utf-8')
print (file_name)
#Receive Segment length
stri = sock.recv(1024)
stri = stri.decode('utf-8')
print (stri)
segment_length = int(stri.split(' ')[1])
nth_segment = random.randint(0, segment_length-1)
while count < segment_length:
    filename = "temp_client/output" + str(nth_segment)
    with open(filename, "wb") as output:
        command = "REQUEST " + str(nth_segment)
        sock.send(command.encode())
        print(command)
        received = sock.recv(4096)
        filesize = int(received.decode('utf-8'))
        total = 0
        print(filesize)
        while True:
            if total >= filesize: break
            received = sock.recv(4096)
            output.write(received)
            total += len(received)
        sock.send("DONE".encode('utf-8'))
        print ("writing file" + str(nth_segment))
        count += 1
        nth_segment += 1
        if nth_segment >= segment_length:
            nth_segment = 0
sock.send("FINISH".encode())
os.chdir("./temp_client/")
filelist = os.listdir()
with open(file_name, "wb") as f:
    for name in filelist:
        input = open(name, "rb")
        f.write(input.read())
        input.close()

