import random

from numpy.polynomial.polynomial import polyval

s = 3
p = 11


def square_and_multiply(x, c, n):
    # z=x^c mod n
    c = '{0:b}'.format(c)  # convert exponent to binary
    z = 1
    l = len(c)

    for i in range(0, l):
        z = z ** 2 % n
        if c[i] == "1":
            z = (z * x) % n

    return int(z)


# finds a primitive root for prime p
# this function was implemented from the algorithm described here:
# http://modular.math.washington.edu/edu/2007/spring/ent/ent-html/node31.html
def find_primitive_root(p):
    if p == 2:
        return 1
    # the prime divisors of p-1 are 2 and (p-1)/2 because
    # p = 2x + 1 where x is a prime
    p1 = 2
    p2 = (p - 1) // p1

    # test random g's until one is found that is a primitive root mod p
    while 1:
        g = random.randint(2, p - 1)
        # g is a primitive root if for all prime factors of p-1, p[i]
        # g^((p-1)/p[i]) (mod p) is not congruent to 1
        if not (square_and_multiply(g, (p - 1) // p1, p) == 1):
            if not square_and_multiply(g, (p - 1) // p2, p) == 1:
                return g


# 1 0
# 2 4
# 3 4
# 4 0
# 5 3

# Primitive root of a prime number n is an integer r between[1, n-1] such that
# the values of r^x(mod n) where x is in range[0, n-2] are different.
# g is the generator
g = find_primitive_root(p)

coeff_lst = [s] + [3, 6, 9]
print(coeff_lst)

publish_lst = []
for element in coeff_lst:
    print(element, g ** element)
    publish_lst.append(g ** element)

eval = 1
i = 1
for idx, val in enumerate(publish_lst):
    eval *= (val ** (i ** idx))

print(eval % p == g ** int(polyval(i, coeff_lst)) % p)
