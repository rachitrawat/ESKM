import os
import re
import socket
import ssl
from subprocess import call, check_output

from core.modules import secret_sharing as ss, misc

debug = False

# local openssl dir
LOCAL_OPENSSL = "/usr/local/ssl/bin/openssl "

GEN_RSA_PRIVATE = (LOCAL_OPENSSL + "genrsa -out private.pem 2048").split()
GEN_RSA_PUBLIC = (LOCAL_OPENSSL + "rsa -in private.pem -outform PEM -pubout -out public.pem").split()
GET_RSA_MODULUS = (LOCAL_OPENSSL + "rsa -noout -modulus -in private.pem").split()
GET_KEY_INFO = (LOCAL_OPENSSL + "rsa -in private.pem -text -inform PEM -noout").split()
CONVERT_SSH_PUB = "ssh-keygen -f public.pem -i -mPKCS8".split()
ROOT_DIR = "/tmp"
CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates"

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 10030))
bindsocket.listen(5)
print("Security Manager is running!")

# Total no of nodes
l = 3
# Threshold no of nodes
k = 2

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("\nGot a connection from %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile=CERT_DIR + "/SM.cert",
                                 keyfile=CERT_DIR + "/SM.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = ROOT_DIR + "/SM/" + fromaddr[0]

    if not os.path.exists(dir_):
        os.makedirs(dir_)
        os.chdir(dir_)
        print("New client has connected!")
        size = str(connstream.recv(4).decode('ascii'))
        print("\nRequested RSA key size: ", size)
        GEN_RSA_PRIVATE[4] = size
        # generate private key
        call(GEN_RSA_PRIVATE)
        # generate public key
        call(GEN_RSA_PUBLIC)
        # convert to ssh format
        pub = (check_output(CONVERT_SSH_PUB)).decode('utf-8')

        with open("id_rsa.pub", "w+") as text_file:
            text_file.write(pub)

        # extract information from private key
        data = (check_output(GET_KEY_INFO)).decode('utf-8')

        # key data in decimal
        e = 65537
        n = int((check_output(GET_RSA_MODULUS)).decode('utf-8').split('=')[1], 16)
        # use regex to extract hex and convert to decimal
        # d = int(re.sub('[^\w]', '', re.findall('privateExponent(?s)(.*)prime1', data)[0]), 16)
        p = int(re.sub('[^\w]', '', re.findall('prime1(?s)(.*)prime2', data)[0]), 16)
        q = int(re.sub('[^\w]', '', re.findall('prime2(?s)(.*)exponent1', data)[0]), 16)
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
        # 2 out of 3 secret sharing over m
        coefficient_lst, shares_lst = ss.split_secret(l, k, m, d)

        # info for share verification
        publish_lst = []
        for element in coefficient_lst:
            publish_lst.append(misc.square_and_multiply(g, element, n))
        if debug:
            print("\nPublished info for verification: ", publish_lst)

        for i in range(1, 4):
            # distribute shares and verification info
            server_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # require a certificate from the cc Node
            ssl_sock = ssl.wrap_socket(server_as_client,
                                       ca_certs=CERT_DIR + "/CA.cert",
                                       cert_reqs=ssl.CERT_REQUIRED)

            print("\nUploading share to CC node %s ..." % i)
            ssl_sock.connect((socket.gethostname(), 4001 + i - 1))
            ssl_sock.send("0".encode('ascii'))
            with open("tmp_data.txt", "w+") as text_file:
                text_file.write(str(shares_lst[i - 1]) + "\n" + str(n) + "\n" + str(publish_lst) + "\n" + str(g))
            misc.send_file("tmp_data.txt", ssl_sock)
            print("Done! Closing connection with CC node %s." % i)
            ssl_sock.close()

    else:
        print("Old client has connected!")

    os.chdir(dir_)
    # send public key to client
    print("\nSending public key to client...")
    misc.send_file("id_rsa.pub", connstream)
    print("Public key sent to client!")

    # finished with client
    print("Done! Closing connection with client.")
    connstream.close()
