import socket
import ssl

from core.modules import misc

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# require a certificate from the server
ssl_sock = ssl.wrap_socket(s,
                           ca_certs="certificates/CA.cert",
                           cert_reqs=ssl.CERT_REQUIRED)

ssl_sock.connect((socket.gethostname(), 10030))

size = input("Enter RSA key size in bits: ")
# request RSA key from server
ssl_sock.send(size.encode('ascii'))

# receive public key
print("\nReceiving public key from SM...")
misc.recv_file("/home/r/.ssh/id_rsa.pub", ssl_sock)
print("Public key received!")

# close socket
print("\nDone! Closing connection with SM.")
ssl_sock.close()
