from core.modules import misc


def verify_share(i, g_exp_share, public_info, q):
    prod = 1
    for idx, val in enumerate(public_info):
        prod *= misc.square_and_multiply(val, i ** idx, q)

    return prod % q == g_exp_share
