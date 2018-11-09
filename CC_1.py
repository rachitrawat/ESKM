import ast
import math
import os
import socket
import ssl
import threading

from core.modules import misc, share_verification as sv, share_refresh as sr

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 4001))
bindsocket.listen(5)
print("CC_1 is running!")
delta = math.factorial(3)
ROOT_DIR = os.getcwd()
node_no = 1
l = 3
k = 2


def refresh_shares():
    threading.Timer(10.0, refresh_shares).start()
    if os.path.isfile("CC_1/share.txt"):
        print("Starting share refresh protocol...")
        with open("CC_1/share.txt") as f:
            content = f.readlines()
        content = [x.strip() for x in content]
        share = (int(content[0]))
        n = (int(content[1]))
        coefficient_lst, shares_lst = sr.refresh_shares(n, l, k)


# refresh_shares()

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("\nGot a connection from %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile=ROOT_DIR + "/certificates/CC_1.cert",
                                 keyfile=ROOT_DIR + "/certificates/CC_1.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = ROOT_DIR + "/CC_1/"
    if not os.path.exists(dir_):
        os.makedirs(dir_)

    # check if SM or client is connecting
    flag = str(connstream.recv(1024).decode('ascii'))
    if flag == "0":
        print("\nSM has connected!")
        # receive key-share
        print("Receiving share...")
        share = str(connstream.recv(1024).decode('ascii'))
        # receive RSA modulus
        print("Receiving RSA modulus...")
        n = int(connstream.recv(1024).decode('ascii'))
        # receive verification values
        print("Receiving verification values...")
        str_lst = connstream.recv(1024).decode('ascii')
        publish_lst = ast.literal_eval(str_lst)
        g = int(connstream.recv(1024).decode('ascii'))

        # share verification
        if not sv.verify_share(node_no, misc.square_and_multiply(g, int(share), n), publish_lst, n):
            print("Share verification: FAILED")
        else:
            print("Share verification: OK")
            with open(dir_ + 'share.txt', 'w+') as the_file:
                the_file.write(share + "\n" + str(n))

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
        print("Sending signature fragment to client...")
        connstream.send(str(x).encode('ascii'))
        print("Sending RSA modulus to client...")
        connstream.send(str(n).encode('ascii'))
        # finished with client
        print("Done! Closing connection with client.")
        connstream.close()
