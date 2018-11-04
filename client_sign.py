import errno
import math
import socket
import ssl
import sys
from socket import error as socket_error

from core.modules import lagrange_interpolation as lp, misc

if sys.argv[1:] == ["debug"]:
    debug = True
else:
    debug = False

# read Encoded Message (EM) from file
# EM will be signed
with open("/tmp/eskm_em.txt") as f:
    content = f.readlines()

em = ''.join(content)
digest = int(em, 16)

x = []
delta = math.factorial(3)
n = 0
e = 65537
k = 2
online_nodes = []

for i in range(1, 4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # require a certificate from the CC node
    ssl_sock = ssl.wrap_socket(s,
                               ca_certs="/home/r/PycharmProjects/ESKM/certificates/CA.cert",
                               cert_reqs=ssl.CERT_REQUIRED)

    print("\nConnecting to CC_%s..." % i)

    try:
        ssl_sock.connect((socket.gethostname(), 4001 + i - 1))
    except socket_error as serr:
        if serr.errno != errno.ECONNREFUSED:
            raise serr
        print("Connection to CC_%s failed!" % i)
        continue

    print("Connected to CC_%s!" % i)
    online_nodes.append(i)

    # client flag
    ssl_sock.send("1".encode('ascii'))

    # request sig from CC nodes
    ssl_sock.send(str(digest).encode('ascii'))

    # receive sig fragment
    print("Receiving sig fragment and modulus from CC_%s..." % i)
    x.append(int(ssl_sock.recv(1024).decode('ascii')))
    n = int(ssl_sock.recv(1024).decode('ascii'))
    print("Sig fragment and modulus received!")

    # close socket
    print("Done! Closing connection with CC_%s..." % i)
    ssl_sock.close()

    # break if we have k shares
    if len(online_nodes) == k:
        break

if len(online_nodes) != k:
    print("\nLess than %s nodes online. Signature generation failed!" % k)
    with open('/tmp/eskm_sig.txt', 'w+') as the_file:
        the_file.write("-1")
else:
    w = 1
    for idx, val in enumerate(online_nodes):
        lambda_i = lp.lambda_eval(val, online_nodes, delta, True)
        w *= misc.square_and_multiply(x[idx], 2 * lambda_i, n)

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
    with open('/tmp/eskm_sig.txt', 'w+') as the_file:
        the_file.write(' '.join(lst2))
