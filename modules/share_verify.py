from modules import utils


def verify_share(i, g_exp_share, public_info, q):
    """ Feldman’s Verifiable Secret Sharing.
    """
    prod = 1
    for idx, val in enumerate(public_info):
        prod *= utils.sq_and_mult(val, i ** idx, q)

    return prod % q == g_exp_share
