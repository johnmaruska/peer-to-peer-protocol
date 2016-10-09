import SocketServer

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    '''
    Who knows?
    Don't read the whole file to the memory
    Try seek function to read specify byte
    Client needs to assemble it.
    '''

    def handle(self):
        nth_segment = 0  # the nth segment
        segment_length = 1024
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        # Send file when client connects
        filename = "input.pdf"
        f = open(filename, "rb")
        print "Send File" + nth_segment
        
        #divide the file & Send
        f.seek(segment_length * k, 1)
        send_segment = f.read(segment_length);
        self.request.sendall(send_segment)

        


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
