from random import randint

from modules import utils


def split_secret(L, K, m, d):
    """ Shamir's K/L secret (d) sharing over m
    """
    coefficient_list = [d]
    shares_lst = []

    for i in range(1, K):
        coefficient_list.append(randint(0, m - 1))

    for i in range(1, L + 1):
        eval = utils.polynomial_eval(coefficient_list, i, m)
        shares_lst.append(eval)

    return coefficient_list, shares_lst
