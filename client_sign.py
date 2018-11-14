import errno
import math
import os
import socket
import ssl
import sys
import time
from socket import error as socket_error

from core.modules import lagrange_interpolation as lp, misc

CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates"
ROOT_DIR = "/tmp"

# Node ID: IP Addr, Port
CC_Map = {1: ["127.0.0.1", 4001],
          2: ["127.0.0.1", 4002],
          3: ["127.0.0.1", 4003]}

os.chdir(ROOT_DIR)

if sys.argv[1:] == ["debug"]:
    debug = True
else:
    debug = False

# read Encoded Message (EM) from file
# EM will be signed
content = misc.read_file("eskm_em.txt")

em = ''.join(content)
digest = int(em, 16)

misc.write_file("eskm_digest.txt", str(digest))

x = [0] * 4
timestamp_dict = {}
delta = math.factorial(3)
n = 0
e = 65537
k = 2
count = 0
timestamp_to_use = 0
while count != 3:
    flag = False
    for i, addr in CC_Map.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # require a certificate from the CC node
        ssl_sock = ssl.wrap_socket(s,
                                   ca_certs=CERT_DIR + "/CA.cert",
                                   cert_reqs=ssl.CERT_REQUIRED)

        print("\nConnecting to CC_%s..." % i)

        try:
            ssl_sock.connect((CC_Map[i][0], CC_Map[i][1]))
        except socket_error as serr:
            if serr.errno != errno.ECONNREFUSED:
                raise serr
            print("Connection to CC_%s failed!" % i)
            continue

        print("Connected to CC_%s!" % i)

        # client flag
        ssl_sock.send("1".encode('ascii'))

        # request sig from CC nodes
        misc.send_file("eskm_digest.txt", ssl_sock)

        # receive sig data
        print("Receiving sig data from CC_%s..." % i)
        misc.recv_file("eskm_cc_sig_data.txt", ssl_sock)

        content = misc.read_file("eskm_cc_sig_data.txt")
        x[i] = int(content[0])
        n = int(content[1])
        timestamp = int(content[2])
        print("Sig data received!")

        if timestamp not in timestamp_dict:
            timestamp_dict[timestamp] = []

        if i not in timestamp_dict[timestamp]:
            timestamp_dict[timestamp].append(i)

        # close socket
        print("Done! Closing connection with CC_%s..." % i)
        ssl_sock.close()

        for timestamp, nodes in timestamp_dict.items():
            if len(nodes) >= k:
                flag = True
                timestamp_to_use = timestamp
                break
        if flag:
            break

    if flag:
        break
    else:
        print("\nRetrying in 5s...")
        count += 1
        time.sleep(5)

if len(timestamp_dict) == 0:
    print("\nLess than %s nodes online. Signature generation failed!" % k)
    misc.write_file("eskm_sig.txt", "-1")
elif timestamp_to_use not in timestamp_dict or len(timestamp_dict[timestamp_to_use]) < k:
    print("\nTimestamps out of sync. Signature generation failed!")
    misc.write_file("eskm_sig.txt", "-1")
else:
    w = 1
    chosen_nodes = timestamp_dict[timestamp_to_use]
    for idx, val in enumerate(chosen_nodes):
        lambda_i = lp.lambda_eval(val, chosen_nodes, delta, True)
        w *= misc.square_and_multiply(x[val], 2 * lambda_i, n)

    four_delta_sq = 4 * delta ** 2

    a = misc.multiplicative_inverse(four_delta_sq, e)
    b = (1 - (four_delta_sq * a)) // e

    threshold_sig = misc.square_and_multiply(w, a, n) * misc.square_and_multiply(digest, b, n)
    threshold_sig %= n

    if debug:
        print("\nThreshold Signature (Decimal):", threshold_sig)

    char_lst = list(hex(threshold_sig)[2:])
    length = len(char_lst)
    lst1 = []
    lst2 = []
    i = 0
    j = 0
    while i < length - 1:
        lst1.append(char_lst[i] + char_lst[i + 1])
        lst2.append(str(int(lst1[j], 16)))
        i += 2
        j += 1

    # write signature to file
    misc.write_file("eskm_sig.txt", ' '.join(lst2))
