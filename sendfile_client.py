import socket
import sys
import random

HOST, PORT = "localhost", 9999
data = " ".join(sys.argv[1:])
# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    # Receive data from the server and shut down
    nth_segment = random.randint(1, 1000)
    count = 0
    while count < 1000:
        str = sock.recv(1024)
        print str
        segment_length = int(str.split(' ')[1])
        filename = "output" + nth_segment
        output = open(filename, "wb")
        command = "REQUEST " + nth_segment
        sock.send(command)
        received = sock.recv(segment_length)
        if not received: break
        output.write(received)
        print "writing file" + nth_segment
        count += 1
        nth_segment += 1
        if(nth_segment > 1000)
            nth_segment = 0



finally:
    sock.close()

print "Sent:     {}".format(data)
print "Received: {}".format(received)