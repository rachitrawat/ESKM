import random

'''
    Evaluates polynomial at x
'''


def polynomial_eval(coeff_lst, x, p):
    deg = len(coeff_lst)
    sum = 0

    for i in range(0, deg):
        sum += coeff_lst[i] * pow(x, i, p)

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
    Return a random safe prime p of key-size bits in size.

'''


def generate_safe_prime(keysize=300):
    while True:
        num = random.randrange(2 ** (keysize - 1), 2 ** keysize)
        num_ = (num - 1) // 2
        if is_prime(num) and is_prime(num_):
            return num


# TODO
# function implementing Chinese remainder theorem
# list m contains all the modulii
# list x contains the remainders of the equations
def crt(m, x):
    # We run this loop while the list of
    # remainders has length greater than 1
    while True:

        # temp1 will contain the new value
        # of A. which is calculated according
        # to the equation m1' * m1 * x0 + m0'
        # * m0 * x1
        temp1 = multiplicative_inverse(m[1], m[0]) * x[0] * m[1] + \
                multiplicative_inverse(m[0], m[1]) * x[1] * m[0]

        # temp2 contains the value of the modulus
        # in the new equation, which will be the
        # product of the modulii of the two
        # equations that we are combining
        temp2 = m[0] * m[1]

        # we then remove the first two elements
        # from the list of remainders, and replace
        # it with the remainder value, which will
        # be temp1 % temp2
        x.remove(x[0])
        x.remove(x[0])
        x = [temp1 % temp2] + x

        # we then remove the first two values from
        # the list of modulii as we no longer require
        # them and simply replace them with the new
        # modulii that  we calculated
        m.remove(m[0])
        m.remove(m[0])
        m = [temp2] + m

        # once the list has only one element left,
        # we can break as it will only  contain
        # the value of our final remainder
        if len(x) == 1:
            break

    # returns the remainder of the final equation
    return x[0]
