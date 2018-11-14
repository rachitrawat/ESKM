import os
import random

'''
    Evaluates polynomial at x
'''


def polynomial_eval(coeff_lst, x, p, modulo=True):
    deg = len(coeff_lst)
    sum = 0

    for i in range(0, deg):
        if modulo:
            sum = (sum * x + coeff_lst[deg - 1 - i]) % p
        else:
            sum = (sum * x + coeff_lst[deg - 1 - i])

    return sum


'''
    Extended Euclidean Algorithm
    i = a_inv mod b
    j = b_inv mod a
    return i
'''


def multiplicative_inverse(a, b):
    x = 0
    y = 1
    lx = 1
    ly = 0
    oa = a
    ob = b
    while b != 0:
        q = a // b
        (a, b) = (b, a % b)
        (x, lx) = ((lx - (q * x)), x)
        (y, ly) = ((ly - (q * y)), y)
    if lx < 0:
        lx += ob
    if ly < 0:
        ly += oa

    return lx


''' 
    find a primitive root for a safe prime p
    g is a primitive root if for all prime factors p_i of (p-1),
    g^((p-1)/p_i) (mod p) is not congruent to 1

'''


def find_primitive_root(p):
    if p == 2:
        return 1

    p1 = (p - 1) // 2
    p2 = (p - 1) // p1

    while True:
        g = random.randint(2, p - 1)
        if not (square_and_multiply(g, p1, p) == 1) and not (square_and_multiply(g, p2, p) == 1):
            return g


'''
    Use python built-in pow()
    Also account for -ve exponent
'''


def square_and_multiply(x, c, n):
    if c < 0:
        x = multiplicative_inverse(x, n)
        c = abs(c)

    return pow(x, c, n)


def is_prime(n, k=11):
    if n == 2 or n == 3:
        return True
    elif n % 2 == 0 or n < 2:
        return False

    x = n - 1
    r = 0

    while x % 2 == 0:
        x = x // 2
        r += 1

    for i in range(1, k + 1):
        if not miller_rabin(n, x, r):
            return False

    return True


'''
    Primality test
'''


def miller_rabin(n, d, r):
    a = random.randint(2, n - 2)
    x = pow(a, d, n)

    if x == 1 or x == n - 1:
        return True

    for i in range(1, r):
        x = pow(x, 2, n)
        if x == n - 1:
            return True

    return False


'''
    Return a random safe prime p of key-size bits in size

'''


def generate_safe_prime(keysize=300):
    while True:
        num = random.randrange(2 ** (keysize - 1), 2 ** keysize)
        num_ = (num - 1) // 2
        if is_prime(num) and is_prime(num_):
            return num


''' Chinese Remainder Theorem '''


def crt(m, x):
    while True:
        temp1 = multiplicative_inverse(m[1], m[0]) * x[0] * m[1] + \
                multiplicative_inverse(m[0], m[1]) * x[1] * m[0]

        temp2 = m[0] * m[1]

        x.remove(x[0])
        x.remove(x[0])
        x = [temp1 % temp2] + x

        m.remove(m[0])
        m.remove(m[0])
        m = [temp2] + m

        if len(x) == 1:
            break

    return x[0]


''' robust file transfer methods '''


def send_file(file_name, socket_obj):
    # max recv bytes size
    BYTES_RECV = 1024

    statinfo = os.stat(file_name)
    file_size = statinfo.st_size

    # encode filesize as 32 bit binary
    fsize_b = bin(file_size)[2:].zfill(32)
    socket_obj.send(fsize_b.encode('ascii'))

    # send file
    f = open(file_name, 'rb')

    while file_size >= BYTES_RECV:
        l = f.read(BYTES_RECV)
        socket_obj.send(l)
        file_size -= BYTES_RECV

    if file_size > 0:
        l = f.read(file_size)
        socket_obj.send(l)

    f.close()


def recv_file(file_name, socket_obj):
    # max recv bytes size
    BYTES_RECV = 1024

    # recv file size
    fsize_b = socket_obj.recv(32).decode('ascii')
    fsize = int(fsize_b, 2)

    # recv file
    f = open(file_name, 'wb')
    file_size = fsize

    while file_size >= BYTES_RECV:
        buff = bytearray()
        while len(buff) < BYTES_RECV:
            buff.extend(socket_obj.recv(BYTES_RECV - len(buff)))
        f.write(buff)
        file_size -= BYTES_RECV

    if file_size > 0:
        buff = bytearray()
        while len(buff) < file_size:
            buff.extend(socket_obj.recv(file_size - len(buff)))
        f.write(buff)

    f.close()


def write_file(file_name, string):
    with open(file_name, 'w+') as f:
        f.write(string)


def read_file(file_name):
    with open(file_name) as f:
        content = f.readlines()
    return content


def ascii_len(s):
    return len(s.encode('ascii'))


def send_string(string, socket_obj):
    size = ascii_len(string)

    # encode string size as 32 bit binary
    fsize_b = bin(size)[2:].zfill(32)
    socket_obj.send(fsize_b.encode('ascii'))

    # send string
    socket_obj.send(string.encode('ascii'))


def recv_string(socket_obj):
    # recv string size
    fsize_b = socket_obj.recv(32).decode('ascii')
    fsize = int(fsize_b, 2)

    # recv string
    return socket_obj.recv(fsize).decode('ascii')
