import ast
import errno
import math
import os
import socket
import ssl
import threading
import time
from socket import error as socket_error
from subprocess import call

from core.modules import misc, share_verification as sv, share_refresh as sr

node_no = 1
bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 4000 + node_no))
bindsocket.listen(5)
delta = math.factorial(3)

l = 0
k = 0

UPDATE_TIMESTAMP = "mv recv_timestamp.txt timestamp.txt".split()

ROOT_DIR = "/tmp/"
CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates/"

CC = "CC_" + str(node_no)
dir_ = ROOT_DIR + CC

if not os.path.exists(dir_):
    os.makedirs(dir_)

os.chdir(dir_)

mutex = threading.Lock()

print(CC + " is running!")


def refresh_shares():
    mutex.acquire()
    threading.Timer(10.0, refresh_shares).start()

    if os.path.isfile("timestamp.txt"):
        with open("timestamp.txt") as f:
            content = f.readlines()
        timestamp = float(content[0])
        new_timestamp = time.time()
        if abs(timestamp - new_timestamp) > 60:
            print("\n*** Starting share refresh protocol ***")

            with open("new_timestamp.txt", "w+") as text_file:
                text_file.write(str(new_timestamp))

            with open("sm_data.txt") as f:
                content = f.readlines()
            share = (int(content[0]))
            n = (int(content[1]))
            l = (int(content[4]))
            k = (int(content[5]))
            coefficient_lst, shares_lst = sr.refresh_shares(n, l, k)

            for i in range(1, 4):
                if i != node_no:
                    cc_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    # require a certificate from the cc Node
                    ssl_sock = ssl.wrap_socket(cc_as_client,
                                               ca_certs=CERT_DIR + "CA.cert",
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
                    # send timestamp
                    misc.send_file("new_timestamp.txt", ssl_sock)
                    choice = ssl_sock.recv(1).decode('ascii')
                    if choice == "1":
                        print("CC node %s agreed to refresh shares!" % i)
                        print("Sending refreshed share to CC node %s..." % i)
                        with open("new_share.txt", "w+") as text_file:
                            text_file.write(str(shares_lst[i - 1]))
                        misc.send_file("new_share.txt", ssl_sock)
                        # recv new share
                        # TODO
                    elif choice == "0":
                        print("CC node %s denied to refresh shares!" % i)
    mutex.release()


def listen():
    while True:
        newsocket, fromaddr = bindsocket.accept()
        mutex.acquire()
        print("\nGot a connection from %s" % str(fromaddr))
        connstream = ssl.wrap_socket(newsocket,
                                     server_side=True,
                                     certfile=CERT_DIR + CC + ".cert",
                                     keyfile=CERT_DIR + CC + ".pkey",
                                     ssl_version=ssl.PROTOCOL_TLSv1)

        # check if SM or client or CC is connecting
        flag = str(connstream.recv(1).decode('ascii'))
        if flag == "0":
            print("\nSM has connected!")
            # receive key-share
            print("Receiving data...")
            misc.recv_file("sm_data.txt", connstream)

            with open('sm_data.txt') as f:
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

            # write timestamp
            with open("timestamp.txt", "w+") as text_file:
                text_file.write(str(time.time()))

            # finished with SM
            print("Done! Closing connection with SM.")
            connstream.close()

        elif flag == "1":
            print("\nClient has connected!")
            # recv digest to be signed
            misc.recv_file("client_digest.txt", connstream)

            with open('client_digest.txt') as f:
                content = f.readlines()
            digest = (int(content[0]))

            with open('sm_data.txt') as f:
                content = f.readlines()
            share = (int(content[0]))
            n = (int(content[1]))
            x = misc.square_and_multiply(digest, 2 * delta * share, n)

            with open("client_sig_data.txt", 'w+') as the_file:
                the_file.write(str(x) + "\n" + str(n))
            print("Sending signature data to client...")
            misc.send_file("client_sig_data.txt", connstream)

            # finished with client
            print("Done! Closing connection with client.")
            connstream.close()

        # share refresh request
        elif flag == "2":
            node_id = connstream.recv(1).decode('ascii')
            print("\nCC node %s has connected!" % node_id)
            misc.recv_file("recv_timestamp.txt", connstream)

            with open("recv_timestamp.txt") as f:
                content = f.readlines()
            recv_timestamp = float(content[0])

            with open("timestamp.txt") as f:
                content = f.readlines()
            timestamp = float(content[0])

            if abs(recv_timestamp - timestamp) > 60:
                print("Timestamp too old. Agree to refresh shares!")
                connstream.send("1".encode('ascii'))
                print("Receiving new share from node %s..." % node_id)
                misc.recv_file("new_share.txt", connstream)
                print("New share received from node %s!" % node_id)
                call(UPDATE_TIMESTAMP)

            else:
                print("Timestamp too recent. Deny to refresh shares!")
                connstream.send("0".encode('ascii'))

            # finished with CC
            print("Done! Closing connection with CC node %s." % node_id)
            connstream.close()

        mutex.release()


listen_thread = threading.Thread(target=listen)
listen_thread.start()
refresh_shares()
