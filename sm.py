import os
import re
import socket
import ssl
from subprocess import call, check_output

from core.modules import secret_sharing as ss

GEN_RSA_PRIVATE = "openssl genrsa -out private.pem 2048".split()
GEN_RSA_PUBLIC = "openssl rsa -in private.pem -outform PEM -pubout -out public.pem".split()
GET_RSA_MODULUS = "openssl rsa -noout -modulus -in private.pem".split()
GET_KEY_INFO = "openssl rsa -in private.pem -text -inform PEM -noout".split()

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 10029))
bindsocket.listen(5)
print("Security Manager is running!")

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("\nGot a connection from %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile="certificates/sm.cert",
                                 keyfile="certificates/sm.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = "sm/" + fromaddr[0] + "/"
    if not os.path.exists(dir_):
        os.makedirs(dir_)
        print("New client has connected!")
    else:
        print("Old client has connected!")

    size = str(connstream.recv(1024).decode('ascii'))
    print("\nRequested RSA key size: ", size)
    GEN_RSA_PRIVATE[3] = dir_ + "private.pem"
    GEN_RSA_PRIVATE[4] = size
    # generate private key
    call(GEN_RSA_PRIVATE)
    # generate public key
    GEN_RSA_PUBLIC[3] = dir_ + "private.pem"
    GEN_RSA_PUBLIC[8] = dir_ + "public.pem"
    call(GEN_RSA_PUBLIC)

    # extract information from private key
    GET_RSA_MODULUS[5] = dir_ + "private.pem"
    GET_KEY_INFO[3] = dir_ + "private.pem"
    data = (check_output(GET_KEY_INFO)).decode('utf-8')

    # key data in decimal
    e = 65537
    n = int((check_output(GET_RSA_MODULUS)).decode('utf-8').split('=')[1], 16)
    # use regex to extract hex
    d = int(re.sub('[^\w]', '', re.findall('privateExponent(?s)(.*)prime1', data)[0]), 16)
    p = int(re.sub('[^\w]', '', re.findall('prime1(?s)(.*)prime2', data)[0]), 16)
    q = int(re.sub('[^\w]', '', re.findall('prime2(?s)(.*)exponent1', data)[0]), 16)
    exp1 = int(re.sub('[^\w]', '', re.findall('exponent1(?s)(.*)exponent2', data)[0]), 16)
    exp2 = int(re.sub('[^\w]', '', re.findall('exponent2(?s)(.*)coefficient', data)[0]), 16)
    coeff = int(re.sub('[^\w]', '', re.findall('coefficient(?s)(.*)', data)[0]), 16)
    totient = (p - 1) * (q - 1)

    # split and share d
    # 2 out of 3
    coefficient_lst, shares_lst = ss.split_secret(3, 2, n, d)

    for i in range(1, 4):
        # distribute shares
        server_as_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # require a certificate from the cc Node
        ssl_sock = ssl.wrap_socket(server_as_client,
                                   ca_certs="certificates/CA.cert",
                                   cert_reqs=ssl.CERT_REQUIRED)

        print("\nUploading share to CC node %s ..." % i)
        ssl_sock.connect((socket.gethostname(), 4001 + i - 1))
        ssl_sock.send(str(shares_lst[i - 1]).encode('ascii'))
        print("Done! Closing connection with CC node %s." % i)
        ssl_sock.close()

    # send public key to client
    print("\nSending public key to client...")
    f = open(dir_ + "public.pem", 'rb')
    l = f.read(1024)
    while l:
        connstream.send(l)
        l = f.read(1024)
    f.close()
    print("Public key sent to client!")

    # finished with client
    print("\nDone! Closing connection with client.")
    connstream.close()
