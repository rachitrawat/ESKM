import math

from core.modules import misc, lagrange_interpolation as lp


def compute_sig(dict, msg, n, N, e):
    x_dict = {}
    w = 1
    # digest = hashlib.sha1(msg.encode("utf-8")).hexdigest()
    # digest = int(digest, 16)
    digest = msg

    delta = math.factorial(n)

    for node, share in dict.items():
        x_dict[node] = misc.square_and_multiply(digest, (2 * delta * share), N)

    for node, x_val in x_dict.items():
        lambda_i_s = int(lp.lambda_eval_s(node, dict.keys(), delta))
        if lambda_i_s < 0:
            x_val = misc.multiplicative_inverse(x_val, N)
        lambda_i_s = abs(lambda_i_s)
        w *= misc.square_and_multiply(x_val, 2 * lambda_i_s, N)

    one, a, b = misc.multiplicative_inverse(4 * (delta ** 2), e, True)
    b = (1 - (4 * (delta ** 2) * a)) // e
    if b < 0:
        digest = misc.multiplicative_inverse(digest, N)
    sig = misc.square_and_multiply(w, a, N) * misc.square_and_multiply(digest, b, N)

    return sig, digest
