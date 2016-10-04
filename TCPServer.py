import socket
import sys

serverPort = 12000  # Determine later.

# Create welcoming socket
try:
    welcomeSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except:  # TODO: Find out what type of exception
    print("Server: Error creating welcoming stream socket.")
    sys.exit(1)

# Bind welcoming socket
try:
    welcomeSocket.bind(('',serverPort))
except:  # TODO: Find out what type of exception
    print("Server: Error binding welcoming socket.")
    sys.exit(1)

try:
    welcomeSocket.listen(1)
except:  # TODO: Find out what type of exception
    print("Server: Error listening for client.")
    sys.exit(1)


print('The server is ready to receive.')

while 1:
    connectionSocket, addr = welcomeSocket.accept()
    # TODO: Actual p2p handling happens here.
    connectionSocket.close()