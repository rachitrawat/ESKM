from random import randint

from core.modules import misc


def refresh_shares(n, l, k):
    coefficient_list = [0]
    shares_lst = []

    # Randomly choose k-1 degree elements from [0,n]
    for i in range(1, k):
        coefficient_list.append(randint(0, n))

    for i in range(1, l + 1):
        eval = misc.polynomial_eval(coefficient_list, i, 1, False)
        shares_lst.append(eval)

    return coefficient_list, shares_lst
