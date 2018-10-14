from functools import reduce
from core.modules import misc


# return lambda_i(x=0)
def lambda_eval(i, lst, p, x=0):
    num = []
    den = []
    for element in lst:
        if element != i:
            num.append(x - element)
            den.append(i - element)

    eval_num = reduce(lambda x, y: x * y, num)
    eval_den = reduce(lambda x, y: x * y, den)

    if eval_den < 0:
        eval_den = p - abs(eval_den)

    return (eval_num * misc.multiplicative_inverse(eval_den, p)) % p


def reconstruct_secret(dict, p, debug):
    sum = 0
    for node, share in dict.items():
        sum += lambda_eval(node, dict.keys(), p) * share

    return sum % p
