import ast
import errno
import math
import os
import socket
import ssl
import threading
from socket import error as socket_error

from core.modules import misc, share_verification as sv, share_refresh as sr

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 4001))
bindsocket.listen(5)
print("CC_1 is running!")
delta = math.factorial(3)
ROOT_DIR = "/tmp"
CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates"
node_no = 1
l = 3
k = 2


def refresh_shares():
    threading.Timer(60.0, refresh_shares).start()
    if os.path.isfile(ROOT_DIR + "/CC_1/sm_data.txt"):
        print("\n*** Starting share refresh protocol ***")
        with open(ROOT_DIR + "/CC_1/sm_data.txt") as f:
            content = f.readlines()
        share = (int(content[0]))
        n = (int(content[1]))
        coefficient_lst, shares_lst = sr.refresh_shares(n, l, k)

        for i in range(1, 4):
            if i != node_no:
                cc_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # require a certificate from the cc Node
                ssl_sock = ssl.wrap_socket(cc_as_client,
                                           ca_certs=CERT_DIR + "/CA.cert",
                                           cert_reqs=ssl.CERT_REQUIRED)

                print("\nConnecting to CC node %s..." % i)
                try:
                    ssl_sock.connect((socket.gethostname(), 4001 + i - 1))
                except socket_error as serr:
                    if serr.errno != errno.ECONNREFUSED:
                        raise serr
                    print("Connection to CC_%s failed!" % i)
                    continue
                print("Connected to CC node %s!" % i)
                # send flag
                ssl_sock.send("2".encode('ascii'))
                # send node no
                ssl_sock.send(str(node_no).encode('ascii'))
                print("Sending refreshed share to CC node %s..." % i)
                with open(ROOT_DIR + "/CC_1/new_share.txt", "w+") as text_file:
                    text_file.write(str(shares_lst[i - 1]))
                misc.send_file(ROOT_DIR + "/CC_1/new_share.txt", ssl_sock)


# refresh_shares()

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("\nGot a connection from %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile=CERT_DIR + "/CC_1.cert",
                                 keyfile=CERT_DIR + "/CC_1.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = ROOT_DIR + "/CC_1/"
    if not os.path.exists(dir_):
        os.makedirs(dir_)

    # check if SM or client or CC is connecting
    flag = str(connstream.recv(1).decode('ascii'))
    if flag == "0":
        print("\nSM has connected!")
        # receive key-share
        print("Receiving data...")
        misc.recv_file(dir_ + "sm_data.txt", connstream)

        with open(dir_ + 'sm_data.txt') as f:
            content = f.readlines()
        share = (int(content[0]))
        n = (int(content[1]))
        publish_lst = ast.literal_eval(content[2])
        g = (int(content[3]))

        # share verification
        if not sv.verify_share(node_no, misc.square_and_multiply(g, int(share), n), publish_lst, n):
            print("Share verification: FAILED")
        else:
            print("Share verification: OK")

        # finished with SM
        print("Done! Closing connection with SM.")
        connstream.close()

    elif flag == "1":
        print("\nClient has connected!")
        # recv digest to be signed
        misc.recv_file(dir_ + "client_digest.txt", connstream)

        with open(dir_ + 'client_digest.txt') as f:
            content = f.readlines()
        digest = (int(content[0]))

        with open(dir_ + 'sm_data.txt') as f:
            content = f.readlines()
        share = (int(content[0]))
        n = (int(content[1]))
        x = misc.square_and_multiply(digest, 2 * delta * share, n)

        with open(dir_ + "client_sig_data.txt", 'w+') as the_file:
            the_file.write(str(x) + "\n" + str(n))
        print("Sending signature data to client...")
        misc.send_file(dir_ + "client_sig_data.txt", connstream)

        # finished with client
        print("Done! Closing connection with client.")
        connstream.close()

    # share refresh request
    elif flag == "2":
        node_id = connstream.recv(1).decode('ascii')
        print("\nCC node %s has connected!" % node_id)
        print("Receiving new share from node %s..." % node_id)
        misc.recv_file(ROOT_DIR + "/CC_1/new_share.txt", connstream)
        print("New share received from node %s!" % node_id)
