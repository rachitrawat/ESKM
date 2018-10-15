from core.modules import misc


def verify_share(i, g_f_i, publish_lst, q):
    prod = 1
    for idx, val in enumerate(publish_lst):
        prod *= misc.square_and_multiply(val, i ** idx, q)

    return prod % q == g_f_i
