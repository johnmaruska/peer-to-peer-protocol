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
    sock.sendall(data + "\n")
    # Receive data from the server and shut down
    filename = "output" + str(random.randint(1, 10))
    output = open(filename, "wb")
    while True:
        received = sock.recv(1024)
        if not received: break
        output.write(received)
        print "writing file.."
finally:
    sock.close()

print "Sent:     {}".format(data)
print "Received: {}".format(received)