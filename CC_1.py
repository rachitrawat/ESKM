import math
import os
import socket
import ssl

from core.modules import misc

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 4001))
bindsocket.listen(5)
print("CC_1 is running!")
delta = math.factorial(3)

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("\nGot a connection from %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile="certificates/CC_1.cert",
                                 keyfile="certificates/CC_1.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = "CC_1/"
    if not os.path.exists(dir_):
        os.makedirs(dir_)

    # check if SM or client is connecting
    flag = str(connstream.recv(1024).decode('ascii'))
    if flag == "0":
        print("\nSM has connected!")
        # receive key-share
        share = str(connstream.recv(1024).decode('ascii'))
        print("Received share successfully!")
        # receive RSA modulus
        n = str(connstream.recv(1024).decode('ascii'))
        print("Received RSA modulus successfully!")

        with open(dir_ + 'share.txt', 'w+') as the_file:
            the_file.write(share + "\n" + n)

        # finished with SM
        print("Done! Closing connection with SM.")
        connstream.close()

    else:
        print("\nClient has connected!")
        # recv digest to be signed
        digest = int(connstream.recv(1024).decode('ascii'))
        with open(dir_ + 'share.txt') as f:
            content = f.readlines()
        content = [x.strip() for x in content]
        share = (int(content[0]))
        n = (int(content[1]))
        x = misc.square_and_multiply(digest, 2 * delta * share, n)
        print("Sending sig fragment to client...")
        connstream.send(str(x).encode('ascii'))
        # finished with client
        print("Done! Closing connection with client.")
        connstream.close()
