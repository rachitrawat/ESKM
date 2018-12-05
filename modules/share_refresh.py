from random import randint

from modules import utils


def refresh_shares(n, L, K):
    """ Proactive Secret Sharing.
    """
    coefficient_list = [0]
    shares_lst = []

    for i in range(1, K):
        coefficient_list.append(randint(0, n - 1))

    for i in range(1, L + 1):
        eval = utils.polynomial_eval(coefficient_list, i, 1, False)
        shares_lst.append(eval)

    return coefficient_list, shares_lst
