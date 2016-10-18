import random
import socket
import sys

HOST, PORT = "localhost", 30000
# the second argument
data = " ".join(sys.argv[1:])
# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    print ("connect!")
    # Receive data from the server and shut down
    count = 0
    stri = sock.recv(1024)
    stri = str(stri)
    print (stri)
    segment_length = int(stri.split(' ')[1])
    print segment_length
    nth_segment = random.randint(0, segment_length)
    while count < segment_length:
        filename = "temp_client/output" + str(nth_segment)
        output = open(filename, "wb")
        print filename
        command = "REQUEST " + str(nth_segment)
        sock.send(command)
        print command
        received = sock.recv(1024)
        while True:
            if not received: break
            output.write(received)
            received = sock.recv(1024)
            print len(received)

        print ("writing file" + str(nth_segment))
        count += 1
        nth_segment += 1
        if nth_segment >= segment_length:
            nth_segment = 0
    sock.send("FINISH")

finally:
    sock.close()
