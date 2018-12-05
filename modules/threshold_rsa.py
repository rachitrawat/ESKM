from modules import utils, lagr_interpolate as lp


def calc_threshold_sig(node_share_dict, digest, delta, n, e):
    """ Shoup’s Threshold RSA Signatures
    """
    x_i = {}
    w = 1

    for node, share in node_share_dict.items():
        x_i[node] = utils.sq_and_mult(digest, 2 * delta * share, n)

    for node, x_i in x_i.items():
        lambda_i = lp.lambda_eval(node, node_share_dict.keys(), delta, True)
        w *= utils.sq_and_mult(x_i, 2 * lambda_i, n)

    four_delta_sq = 4 * delta ** 2

    a = utils.mult_inv(four_delta_sq, e)
    b = (1 - (four_delta_sq * a)) // e

    threshold_sig = utils.sq_and_mult(w, a, n) * utils.sq_and_mult(digest, b, n)

    return threshold_sig % n
