import os
import re
import shutil
import socket
import ssl
import time
from subprocess import call, check_output

from core.modules import secret_sharing as ss, misc

debug = False

# local openssl (patched)
LOCAL_OPENSSL = "/usr/local/ssl/bin/openssl "
# bin openssl
OPENSSL = "/usr/bin/openssl "

supported_key_size = ["1024", "2048", "4096"]

GEN_RSA_PRIVATE = (LOCAL_OPENSSL + "genrsa -out private.pem 2048").split()
GEN_RSA_DUMMY = (OPENSSL + "genrsa -out dummy.pem 2048").split()
GEN_RSA_PUBLIC = (LOCAL_OPENSSL + "rsa -in private.pem -outform PEM -pubout -out public.pem").split()
GET_RSA_MODULUS = (LOCAL_OPENSSL + "rsa -noout -modulus -in private.pem").split()
GET_KEY_INFO = (LOCAL_OPENSSL + "rsa -in private.pem -text -inform PEM -noout").split()
CONVERT_SSH_PUB = "ssh-keygen -f public.pem -i -mPKCS8".split()

ROOT_DIR = "/tmp"
CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates"

# Total no of nodes
l = 3
# Threshold no of nodes
k = 2

# Node ID: IP Addr, Port
CC_Map = {1: ["127.0.0.1", 4001],
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

    dir_ = ROOT_DIR + "/SM/" + fromaddr[0]

    if not os.path.exists(dir_):
        os.makedirs(dir_)
    os.chdir(dir_)

    key_size = str(connstream.recv(4).decode('ascii'))
    print("\nRequested RSA key size: ", key_size)
    if key_size not in supported_key_size:
        key_size = "2048"
    GEN_RSA_PRIVATE[4] = key_size
    GEN_RSA_DUMMY[4] = key_size

    # generate private key
    call(GEN_RSA_PRIVATE)
    # generate public key
    call(GEN_RSA_PUBLIC)
    # convert pubkey to ssh format
    pub = (check_output(CONVERT_SSH_PUB)).decode('ascii')
    misc.write_file("id_rsa.pub", pub)

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
    d = misc.multiplicative_inverse(e, m)
    g_p = misc.find_primitive_root(p)
    g_q = misc.find_primitive_root(q)
    g = misc.crt([g_p, g_q], [p, q])
    g = misc.square_and_multiply(g, 2, n)

    # split and share d
    # k out of l secret sharing over m
    coefficient_lst, shares_lst = ss.split_secret(l, k, m, d)

    # info for share verification
    feldman_info = []
    for element in coefficient_lst:
        feldman_info.append(misc.square_and_multiply(g, element, n))
    if debug:
        print("\nPublished info for verification: ", feldman_info)

    timestamp = int(time.time())

    for i, addr in CC_Map.items():
        # distribute shares and verification info
        server_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # require a certificate from the cc Node
        ssl_sock = ssl.wrap_socket(server_as_client,
                                   ca_certs=CERT_DIR + "/CA.cert",
                                   cert_reqs=ssl.CERT_REQUIRED)

        print("\nUploading share to CC node %s ..." % i)
        ssl_sock.connect((addr[0], addr[1]))
        ssl_sock.send("0".encode('ascii'))
        sm_data_str = str(shares_lst[i - 1]) + "\n" + str(n) + "\n" + str(feldman_info) + "\n" + str(g) + "\n" + str(
            l) + "\n" + str(k) + "\n" + str(timestamp)
        misc.write_file("sm_data.txt", sm_data_str)
        misc.send_file("sm_data.txt", ssl_sock)
        print("Done! Closing connection with CC node %s." % i)
        ssl_sock.close()

    # send public key to client
    print("\nSending public key to client...")
    misc.send_file("id_rsa.pub", connstream)
    print("Public key sent to client!")
    # generate dummy private key
    call(GEN_RSA_DUMMY)
    # send dummy private key to client
    print("Sending dummy private key to client...")
    misc.send_file("dummy.pem", connstream)
    print("Dummy private key sent to client!")

    # finished with client
    print("Done! Closing connection with client.")
    # remove files
    shutil.rmtree(dir_)
    connstream.close()
