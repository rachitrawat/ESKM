import socket, ssl, pprint

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# require a certificate from the server
ssl_sock = ssl.wrap_socket(s,
                           ca_certs="certificates/CA.cert",
                           cert_reqs=ssl.CERT_REQUIRED)

ssl_sock.connect((socket.gethostname(), 10021))

# print(repr(ssl_sock.getpeername()))
# pprint.pprint(ssl_sock.getpeercert())
# pprint.pformat(ssl_sock.getpeercert()))

size = input("Enter RSA key size in bits: ")
# request RSA key from server
ssl_sock.send(size.encode('ascii'))

# receive public key
print("\nReceiving public key from server...")
with open('client/public.pem', 'wb') as f:
    while True:
        data = ssl_sock.recv(1024)
        if not data:
            break
        f.write(data)
print("Public key received!")

# close socket
print("\nClosing socket!")
ssl_sock.close()
