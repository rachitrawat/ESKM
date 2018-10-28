import os
import socket
import ssl

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 4001))
bindsocket.listen(5)
print("CC node 1 is running!")

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("\nGot a connection from %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile="certificates/node1.cert",
                                 keyfile="certificates/node1.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = "cc_1/"
    if not os.path.exists(dir_):
        os.makedirs(dir_)

    # receive key-share
    share = str(connstream.recv(1024).decode('ascii'))
    print("\nReceived share successfully!")

    with open(dir_ + 'share.txt', 'w+') as the_file:
        the_file.write(share)

    # finished with SM
    print("\nDone! Closing connection with SM.")
    connstream.close()
