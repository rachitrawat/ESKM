import socket
import ssl
import os
from subprocess import call

GEN_RSA_PRIVATE = "openssl genrsa -out private.pem 2048".split()
GEN_RSA_PUBLIC = "openssl rsa -in private.pem -outform PEM -pubout -out public.pem".split()

bindsocket = socket.socket()
bindsocket.bind((socket.gethostname(), 10029))
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
