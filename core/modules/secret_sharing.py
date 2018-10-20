from random import randint

from core.modules import misc


# shamir secret sharing

def split_secret(n, k, p, s):
    coefficient_list = [s]
    shares_lst = []

    # Randomly choose k-1 degree elements in Zp
    for i in range(1, k):
        coefficient_list.append(randint(0, p - 1))

    print("\nPolynomial co-efficients: ", coefficient_list)

    # s(i) = f(i) mod p
    for i in range(1, n + 1):
        eval = misc.polynomial_eval(coefficient_list, i) % p
        shares_lst.append(eval)

    return coefficient_list, shares_lst
