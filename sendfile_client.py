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
    print "connect!"
    # Receive data from the server and shut down
    nth_segment = random.randint(1, 100)
    count = 0
    stri = sock.recv(1024)
    print stri
    segment_length = int(stri.split(' ')[1])
    while count < 100:
        filename = "output" + str(nth_segment)
        output = open(filename, "wb")
        command = "REQUEST " + str(nth_segment)
        sock.send(command)
        received = sock.recv(segment_length)
        if not received: break
        output.write(received)
        print "writing file" + str(nth_segment)
        count += 1
        nth_segment += 1
        if nth_segment > 100:
            nth_segment = 0

    sock.send("FINISH")

    f = open("ans.txt", "wb")
    for i in xrange(0, 101):
        filename = "output" + str(i)
        fi = open(filename, "rb")
        s = fi.read()
        f.write(s)

finally:
    sock.close()

print "Sent:     {}".format(data)
print "Received: {}".format(received)