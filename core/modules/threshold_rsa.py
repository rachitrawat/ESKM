from core.modules import misc, lagrange_interpolation as lp


def compute_threhold_sig(node_share_dict, digest, delta, n, e):
    x_i = {}
    w = 1

    for node, share in node_share_dict.items():
        x_i[node] = misc.square_and_multiply(digest, 2 * delta * share, n)

    for node, x_i in x_i.items():
        lambda_i = int(lp.lambda_eval_s(node, node_share_dict.keys(), delta))
        if lambda_i < 0:
            x_i = misc.multiplicative_inverse(x_i, n)
        lambda_i = abs(lambda_i)
        w *= misc.square_and_multiply(x_i, 2 * lambda_i, n)

    one, a, b = misc.multiplicative_inverse(4 * delta ** 2, e, True)
    b = (1 - (4 * (delta ** 2) * a)) // e
    if b < 0:
        digest = misc.multiplicative_inverse(digest, n)
    threshold_sig = misc.square_and_multiply(w, a, n) * misc.square_and_multiply(digest, b, n)

    return threshold_sig % n
