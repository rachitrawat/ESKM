from functools import reduce

from modules import utils


def lambda_eval(i, lst, p, flag=False):
    """ Lagrange interpolation
        return lambda(0)
    """
    num = []
    den = []
    for element in lst:
        if element != i:
            num.append(element)
            den.append(element - i)

    eval_num = reduce(lambda x, y: x * y, num)
    eval_den = reduce(lambda x, y: x * y, den)

    if not flag:
        if eval_den < 0:
            eval_den = p - abs(eval_den)

        return (eval_num * utils.mult_inv(eval_den, p)) % p

    return eval_num * p // eval_den  # p is delta


def reconstruct_secret(dict, p):
    sum = 0
    for node, share in dict.items():
        sum += lambda_eval(node, dict.keys(), p) * share

    return sum % p
