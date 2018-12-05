import socket
import ssl
from subprocess import call

from modules import utils

CERT_DIR = "/home/r/PycharmProjects/ESKM/certificates"
SET_PERM = "./fix_perm.sh"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# require a certificate from the server
ssl_sock = ssl.wrap_socket(s,
                           ca_certs=CERT_DIR + "/CA.cert",
                           cert_reqs=ssl.CERT_REQUIRED)

ssl_sock.connect(("127.0.0.1", 10030))

supported_key_size = ["1024", "2048", "4096"]
print("Supported key-size: 1024, 2048 (default), 4096")
size = input("Enter RSA key-size in bits: ")

if size not in supported_key_size:
    size = "2048"

print("Requesting %s bit RSA key..." % size)
ssl_sock.send(size.encode('ascii'))

print("\nReceiving public key from SM...")
utils.recv_file("/home/r/.ssh/id_rsa.pub", ssl_sock)
print("Public key received!")
print("\nReceiving dummy private key from SM...")
utils.recv_file("/home/r/.ssh/id_rsa", ssl_sock)
print("Dummy private key received!")
call(SET_PERM)

print("\nDone! Closing connection with SM.")
ssl_sock.close()
