import socket
import ssl
import os
from subprocess import call, check_output
import re

GEN_RSA_PRIVATE = "openssl genrsa -out private.pem 2048".split()
GEN_RSA_PUBLIC = "openssl rsa -in private.pem -outform PEM -pubout -out public.pem".split()
GET_RSA_MODULUS = "openssl rsa -noout -modulus -in private.pem".split()
GET_KEY_INFO = "openssl rsa -in private.pem -text -inform PEM -noout".split()

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 10020))
bindsocket.listen(5)
print("Security Manager is running!")

while True:
    newsocket, fromaddr = bindsocket.accept()
    print("Got a connection from %s" % str(fromaddr))
    connstream = ssl.wrap_socket(newsocket,
                                 server_side=True,
                                 certfile="certificates/server.cert",
                                 keyfile="certificates/server.pkey",
                                 ssl_version=ssl.PROTOCOL_TLSv1)

    dir_ = "sm/" + fromaddr[0] + "/"
    if not os.path.exists(dir_):
        os.makedirs(dir_)
        print("New client has connected!")
    else:
        print("Old client has connected!")

    size = str(connstream.recv(1024).decode('ascii'))
    print("\nReceived RSA key size: ", size)
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
    n = int((check_output(GET_RSA_MODULUS)).decode('utf-8').split('=')[1], 16)
    data = (check_output(GET_KEY_INFO)).decode('utf-8')

    # key data in decimal
    e = 65537
    # use regex to extract hex
    d = int(re.sub('[^\w]', '', re.findall('privateExponent(?s)(.*)prime1', data)[0]), 16)
    p = int(re.sub('[^\w]', '', re.findall('prime1(?s)(.*)prime2', data)[0]), 16)
    q = int(re.sub('[^\w]', '', re.findall('prime2(?s)(.*)exponent1', data)[0]), 16)
    exp1 = int(re.sub('[^\w]', '', re.findall('exponent1(?s)(.*)exponent2', data)[0]), 16)
    exp2 = int(re.sub('[^\w]', '', re.findall('exponent2(?s)(.*)coefficient', data)[0]), 16)
    coeff = int(re.sub('[^\w]', '', re.findall('coefficient(?s)(.*)', data)[0]), 16)
    totient = (p - 1) * (q - 1)

    # split d
    # TODO

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
    print("\nClient Disconnected!")
    connstream.close()
