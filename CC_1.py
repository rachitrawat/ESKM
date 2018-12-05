import ast
import errno
import math
import os
import socket
import ssl
import threading
import time
from socket import error as socket_error

from modules import share_refresh as sr, share_verify as sv
from modules import utils

UPDATE_TIMESTAMP = "cp new_timestamp.txt timestamp.txt".split()

WORK_DIR = "/tmp/"
CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates/"

# Node ID: IP Address, Port
CC_Map = {1: ["127.0.0.1", 4001],
          2: ["127.0.0.1", 4002],
          3: ["127.0.0.1", 4003]}

# global variables
SELF_ID = 1
share = 0
n = 0
feldman_info = []
g = 0
L = 0
K = 0
timestamp = 0
expected_timestamp = 0
to_send_refresh_data = {}
recvd_refresh_data = {}
count = 0

CC = "CC_" + str(SELF_ID)
dir_ = WORK_DIR + CC

if not os.path.exists(dir_):
    os.makedirs(dir_)

os.chdir(dir_)

mutex = threading.Lock()

bindsocket = socket.socket()
bindsocket.bind((CC_Map[SELF_ID][0], CC_Map[SELF_ID][1]))
bindsocket.listen(5)
delta = math.factorial(3)
print(CC + " is running!")


def set_vars():
    global share, n, feldman_info, g, L, K, timestamp
    content = utils.read_file("sm_data.txt")
    share = int(content[0])
    n = int(content[1])
    feldman_info = ast.literal_eval(content[2])
    g = int(content[3])
    L = int(content[4])
    K = int(content[5])
    timestamp = int(content[6])


def start_refresh_protocol():
    threading.Timer(10.0, start_refresh_protocol).start()
    mutex.acquire()
    global timestamp, expected_timestamp, share, count

    if os.path.isfile("sm_data.txt") and count <= 2:
        set_vars()
        expected_timestamp = timestamp + 60
        print("\n*** Share Refresh Protocol ***")
        print("Current Timestamp:", timestamp)
        print("Expected Timestamp:", expected_timestamp)

        if expected_timestamp in to_send_refresh_data:
            print("Random zero polynomial already exists!")
        else:
            to_send_refresh_data[expected_timestamp] = {}
            recvd_refresh_data[expected_timestamp] = {}

            print("Creating a random zero polynomial...")
            coefficient_lst, shares_lst = sr.refresh_shares(n, L, K)

            for idx, val in enumerate(shares_lst):
                to_send_refresh_data[expected_timestamp][idx + 1] = val

            # self share
            recvd_refresh_data[expected_timestamp][SELF_ID] = shares_lst[SELF_ID - 1]

        # fetch new shares from other CC nodes
        for i, addr in CC_Map.items():
            # do not fetch share again if share was already fetched earlier for a given timestamp
            if i != SELF_ID and i not in recvd_refresh_data[expected_timestamp]:
                cc_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # require a certificate from the CC Node
                ssl_sock = ssl.wrap_socket(cc_as_client,
                                           ca_certs=CERT_DIR + "CA.cert",
                                           cert_reqs=ssl.CERT_REQUIRED)

                print("\nConnecting to CC node %s..." % i)
                try:
                    ssl_sock.connect((addr[0], addr[1]))
                except socket_error as serr:
                    if serr.errno != errno.ECONNREFUSED:
                        raise serr
                    print("Connection to CC_%s failed!" % i)
                    continue
                print("Connected to CC node %s!" % i)

                ssl_sock.send("2".encode('ascii'))  # send flag
                ssl_sock.send(str(SELF_ID).encode('ascii'))
                utils.send_string(str(expected_timestamp), ssl_sock)

                utils.recv_file("recv_share.txt", ssl_sock)
                content = utils.read_file("recv_share.txt")
                recv_share = int(content[0])
                recv_timestamp = int(content[1])

                if recv_timestamp != "-1" and recv_timestamp == expected_timestamp:
                    print("Timestamp:OK")
                    if recv_share != "-1":
                        print("Share:OK")
                    else:
                        print("Share:FAIL")
                        continue
                else:
                    print("Timestamp:FAIL")
                    continue

                recvd_refresh_data[expected_timestamp][i] = recv_share

        print("\nShares:%s Required:%s" % (len(recvd_refresh_data[expected_timestamp]), K))
        count += 1
        print("Iteration:%s" % count)

        if count == 3:
            refresh_time = abs(expected_timestamp - int(time.time()))
            print("Refreshing shares in %s seconds..." % refresh_time)
            threading.Timer(refresh_time, refresh_share).start()
    mutex.release()


def refresh_share():
    global count
    if len(recvd_refresh_data[expected_timestamp]) >= K:
        sum = share
        for node, new_share in recvd_refresh_data[expected_timestamp].items():
            sum += new_share

        # update everything
        utils.write_file("sm_data.txt",
                         str(sum) + "\n" + str(
                             n) + "\n" + str(
                             feldman_info) + "\n" + str(g) + "\n" + str(
                             L) + "\n" + str(K) + "\n" + str(expected_timestamp))
        print("Shares refreshed!")
        print("Removing old shares...")
        recvd_refresh_data.pop(expected_timestamp)
        to_send_refresh_data.pop(expected_timestamp)
    else:
        print("Share refresh failed!")
    count = 0


def listen():
    while True:
        newsocket, fromaddr = bindsocket.accept()
        mutex.acquire()
        global share, g, n, feldman_info, timestamp, expected_timestamp
        print("\nGot a connection from %s" % str(fromaddr))
        connstream = ssl.wrap_socket(newsocket,
                                     server_side=True,
                                     certfile=CERT_DIR + CC + ".cert",
                                     keyfile=CERT_DIR + CC + ".pkey",
                                     ssl_version=ssl.PROTOCOL_TLSv1)

        # check if SM or client or CC is connecting
        flag = str(connstream.recv(1).decode('ascii'))

        # SM has connected to send key-share
        if flag == "0":
            print("\nSM has connected!")
            print("Receiving key-share...")
            utils.recv_file("sm_data.txt", connstream)
            set_vars()

            # feldman share verification
            if not sv.verify_share(SELF_ID, utils.sq_and_mult(g, int(share), n), feldman_info, n):
                print("Share verification:FAILED")
            else:
                print("Share verification:OK")

            print("Done! Closing connection with SM.")
            connstream.close()

        # client has connected to collect signature fragment
        elif flag == "1":
            set_vars()
            print("\nClient has connected!")
            # digest to be signed
            utils.recv_file("client_digest.txt", connstream)

            content = utils.read_file("client_digest.txt")
            digest = int(content[0])

            x = utils.sq_and_mult(digest, 2 * delta * share, n)

            utils.write_file("client_sig_data.txt", str(x) + "\n" + str(n) + "\n" + str(timestamp))
            print("Sending signature data to client...")
            utils.send_file("client_sig_data.txt", connstream)

            print("Done! Closing connection with client.")
            connstream.close()

        # CC has connected to fetch new shares
        elif flag == "2":
            node_id = int(connstream.recv(1).decode('ascii'))
            print("\nCC node %s has connected to fetch new shares!" % node_id)

            recv_expected_timestamp = int(utils.recv_string(connstream))

            str1 = "-1"
            str2 = "-1"

            if recv_expected_timestamp == expected_timestamp and recv_expected_timestamp in to_send_refresh_data:
                print("Requested Timestamp:OK")
                str2 = str(recv_expected_timestamp)
                if node_id in to_send_refresh_data[recv_expected_timestamp]:
                    print("Requested Share:OK")
                    str1 = str(to_send_refresh_data[recv_expected_timestamp][node_id])
                else:
                    print("Requested Share:FAIL")
            else:
                print("Requested Timestamp:FAIL")

            print("Sending refresh data to node %s..." % node_id)
            utils.write_file("new_share.txt", str1 + "\n" + str2)
            utils.send_file("new_share.txt", connstream)

            print("Done! Closing connection with CC node %s." % node_id)
            connstream.close()

        mutex.release()


listen_thread = threading.Thread(target=listen)
listen_thread.start()
start_refresh_protocol()
