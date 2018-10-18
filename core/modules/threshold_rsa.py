from core.modules import misc, lagrange_interpolation as lp


def compute_threhold_sig(node_share_dict, digest, delta, n, e):
    x_i = {}
    w = 1

    for node, share in node_share_dict.items():
        x_i[node] = misc.square_and_multiply(digest, 2 * delta * share, n)

    for node, x_i in x_i.items():
        lambda_i = lp.lambda_eval(node, node_share_dict.keys(), delta, True)
        w *= misc.square_and_multiply(x_i, 2 * lambda_i, n)

    four_delta_sq = 4 * delta ** 2

    a = misc.multiplicative_inverse(four_delta_sq, e)
    b = (1 - (four_delta_sq * a)) // e

    threshold_sig = misc.square_and_multiply(w, a, n) * misc.square_and_multiply(digest, b, n)

    return threshold_sig % n
