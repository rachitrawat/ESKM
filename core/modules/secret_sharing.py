from random import randint
from core.modules import misc


def split_secret(n, k, p, s, debug=False):
    coeff_list = [s]
    f_eval_list = []

    # Randomly choose k-1 degree elements in Zp
    for i in range(1, k):
        coeff_list.append(randint(0, p - 1))

    print("\nPolynomial co-efficients: ", coeff_list)

    # Compute f(i) mod p
    for i in range(1, n + 1):
        eval = misc.polynomial_eval(coeff_list, i) % p
        f_eval_list.append(eval)
        if debug:
            print("f(%s) mod %s = %s" % (i, p, eval))

    # return f(i)
    return f_eval_list
