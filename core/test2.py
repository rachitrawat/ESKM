import random

from core.modules import secret_sharing as ss, threshold_rsa as tr, \
    misc


def split_verify(s, M):
    n = int(input("\nEnter total nodes: "))
    k = int(input("Enter threshold: "))
    p = M

    # share distribution

    coeff_lst, f_eval_lst = (ss.split_secret(n, k, p, s))
    print("\nEvaluated polynomial: ", f_eval_lst)

    # select k random nodes
    # dict[node_i]= f(i)
    dict = {}
    while True:
        if len(dict) == k:
            break
        i = random.randint(1, n)
        if i not in dict:
            dict[i] = f_eval_lst[i - 1]

    return n, dict


# threshold RSA

b_rsa = int(input("\nEnter bit size for RSA primes: "))
p_rsa = misc.generateLargePrime(b_rsa)
while True:
    q_rsa = misc.generateLargePrime(b_rsa)
    if q_rsa != p_rsa:
        break
totient_rsa = (p_rsa - 1) * (q_rsa - 1)
N = p_rsa * q_rsa
print("p:", p_rsa)
print("q:", q_rsa)
print("totient (phi):", totient_rsa)
e = 65537
d = misc.multiplicative_inverse(e, totient_rsa)
print("Public key (N,e):", N, e)
print("Private key (d):", d)

msg = int(input("\nEnter message to be signed: "))
n, dict = split_verify(d, totient_rsa)
sig_orig = misc.square_and_multiply(msg, d, N)
dec_orig = misc.square_and_multiply(sig_orig, e, N)
sig, digest = tr.compute_sig(dict, msg, n, N, e)
dec = misc.square_and_multiply(sig, e, N)
print(sig_orig, dec_orig, sig, dec)
