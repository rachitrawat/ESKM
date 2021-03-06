import errno
import os
import re
import shutil
import socket
import ssl
import time
from socket import error as socket_error
from subprocess import call, check_output

from modules import secret_sharer as ss, utils

debug = False

# local openssl (patched)
LOCAL_OPENSSL = "/usr/local/ssl/bin/openssl "
# bin openssl
OPENSSL = "/usr/bin/openssl "

supported_key_sizes = ["1024", "2048", "4096"]

GEN_RSA_PRIVATE = (LOCAL_OPENSSL + "genrsa -out private.pem 2048").split()
GEN_RSA_PUBLIC = (LOCAL_OPENSSL + "rsa -in private.pem -outform PEM -pubout -out public.pem").split()
GET_RSA_MODULUS = (LOCAL_OPENSSL + "rsa -noout -modulus -in private.pem").split()
GET_KEY_INFO = (LOCAL_OPENSSL + "rsa -in private.pem -text -inform PEM -noout").split()
CONVERT_TO_SSH_PUB = "ssh-keygen -f public.pem -i -mPKCS8".split()

WORK_DIR = "/tmp"
CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates"

# Total no of nodes
L = 3
# Threshold no of nodes
K = 2

# Node ID: IP address, Port
CC_info_dict = {1: ["127.0.0.1", 4001],
                2: ["127.0.0.1", 4002],
                3: ["127.0.0.1", 4003]}

bindsocket = socket.socket()
bindsocket.bind(("127.0.0.1", 10030))
bindsocket.listen(5)
print("Security Manager is running!")

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("\nGot a connection from client %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile=CERT_DIR + "/SM.cert",
                                 keyfile=CERT_DIR + "/SM.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = WORK_DIR + "/SM/" + fromaddr[0]

    if not os.path.exists(dir_):
        os.makedirs(dir_)
    os.chdir(dir_)

    key_size = str(connstream.recv(4).decode('ascii'))
    print("\nRequested RSA key size: ", key_size)
    if key_size not in supported_key_sizes:
        key_size = "2048"
    GEN_RSA_PRIVATE[4] = key_size

    # generate private key
    call(GEN_RSA_PRIVATE)
    # generate public key
    call(GEN_RSA_PUBLIC)
    # convert pubkey to ssh format
    pub = (check_output(CONVERT_TO_SSH_PUB)).decode('ascii')
    utils.write_file("id_rsa.pub", pub)

    # extract information from private key
    data = (check_output(GET_KEY_INFO)).decode('ascii')

    # use regex to extract hex and convert to decimal
    e = 65537
    n = int((check_output(GET_RSA_MODULUS)).decode('ascii').split('=')[1], 16)
    p = int(re.sub('[^\w]', '', re.findall('prime1(?s)(.*)prime2', data)[0]), 16)
    q = int(re.sub('[^\w]', '', re.findall('prime2(?s)(.*)exponent1', data)[0]), 16)
    # d = int(re.sub('[^\w]', '', re.findall('privateExponent(?s)(.*)prime1', data)[0]), 16)
    # exp1 = int(re.sub('[^\w]', '', re.findall('exponent1(?s)(.*)exponent2', data)[0]), 16)
    # exp2 = int(re.sub('[^\w]', '', re.findall('exponent2(?s)(.*)coefficient', data)[0]), 16)
    # coeff = int(re.sub('[^\w]', '', re.findall('coefficient(?s)(.*)', data)[0]), 16)
    totient = (p - 1) * (q - 1)
    p_ = (p - 1) // 2
    q_ = (q - 1) // 2
    m = p_ * q_
    d = utils.mult_inv(e, m)
    g_p = utils.find_primitive_root(p)
    g_q = utils.find_primitive_root(q)
    g = utils.crt([g_p, g_q], [p, q])
    g = utils.sq_and_mult(g, 2, n)

    # split and share d
    # K out of L secret sharing over m
    coefficient_lst, shares_lst = ss.split_secret(L, K, m, d)

    # info for share verification
    feldman_info = []
    for element in coefficient_lst:
        feldman_info.append(utils.sq_and_mult(g, element, n))
    if debug:
        print("\nPublished info for verification: ", feldman_info)

    # distribute shares and verification info
    timestamp = int(time.time())
    for i, addr in CC_info_dict.items():
        server_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # require a certificate from the CC Node
        ssl_sock = ssl.wrap_socket(server_as_client,
                                   ca_certs=CERT_DIR + "/CA.cert",
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
        print("\nUploading share to CC node %s ..." % i)
        ssl_sock.send("0".encode('ascii'))
        sm_data_str = str(shares_lst[i - 1]) + "\n" + str(n) + "\n" + str(feldman_info) + "\n" + str(g) + "\n" + str(
            L) + "\n" + str(K) + "\n" + str(timestamp)
        utils.write_file("sm_data.txt", sm_data_str)
        utils.send_file("sm_data.txt", ssl_sock)
        print("Done! Closing connection with CC node %s." % i)
        ssl_sock.close()

    print("\nSending public key to client...")
    utils.send_file("id_rsa.pub", connstream)
    print("Public key sent to client!")
    print("Sending dummy private key to client...")
    utils.send_file("/tmp/dummy.pem", connstream)
    print("Dummy private key sent to client!")

    print("Done! Closing connection with client.")
    shutil.rmtree(dir_)  # remove shares
    connstream.close()
