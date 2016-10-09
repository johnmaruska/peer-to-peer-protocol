import SocketServer,os

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
    tracker = []

    def handle(self):
        nth_segment = 0  # the nth segment
        # self.request is the TCP socket connected to the client
        # Send file when client connects
        filename = "input.pdf"
        f = open(filename, "rb")
        size = os.path.getsize(filename)
        print size
        segment_length = size / 100
        '''
        Server send the segment length at very first.
            SEGMENT [size]
        Client should ask the segment first, or return the segment number it received last time.
        And the format should be:
            SUCCESS [number]
            REQUEST [number]
            FINISH

        '''
        msg = "SEGMENT " + str(segment_length)
        print msg
        self.request.sendall(msg)
        res = ""
        res = self.request.recv(1024)
        # divide the file & Send
        while True:
            if res == "FINISH":
                break
            else:
                res_list = res.split(' ')
                if res_list == "SUCCESS":
                    nth_segment = int(res_list[1])
                elif res_list == "REQUEST":
                    nth_segment = int(res_list[1])
                print "Send File" + str(nth_segment)
                f.seek(nth_segment * segment_length, 0)
                send_segment = f.read(segment_length)
                self.request.sendall(send_segment)
                res = self.request.recv(1024)
        


if __name__ == "__main__":
    HOST, PORT = "localhost", 9999

    # Create the server, binding to localhost on port 9999
    server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
