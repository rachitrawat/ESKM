from functools import reduce
from core.modules import misc


# return lambda_i(x=0)
def lambda_eval(i, lst, p):
    num = []
    den = []
    for element in lst:
        if element != i:
            num.append(element)
            den.append(element - i)

    eval_num = reduce(lambda x, y: x * y, num)
    eval_den = reduce(lambda x, y: x * y, den)

    if eval_den < 0:
        eval_den = p - abs(eval_den)

    return (eval_num * misc.multiplicative_inverse(eval_den, p)) % p


# return lambda_i(x=0)
def lambda_eval_s(i, lst, delta):
    num = []
    den = []
    for element in lst:
        if element != i:
            num.append(element)
            den.append(element - i)

    eval_num = reduce(lambda x, y: x * y, num)
    eval_den = reduce(lambda x, y: x * y, den)

    return eval_num * (delta / eval_den)


def reconstruct_secret(dict, p):
    sum = 0
    for node, share in dict.items():
        sum += lambda_eval(node, dict.keys(), p) * share

    return sum % p
