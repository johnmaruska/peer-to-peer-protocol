import socket
import sys

serverName = 'servername'  # TODO: What is server name?
serverPort = 12000  # Must match TCPServer.py

# Create client socket.
try:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except:
    print("Client: Error making client socket.")
    sys.exit(1)

# Connect client to server.
try:
    clientSocket.connect((serverName, serverPort))
except:
    print("Client: Error connecting to server (%s, %s)." % (serverName, serverPort))
# TODO: Actual p2p protocol stuff goes here.

clientSocket.close()
