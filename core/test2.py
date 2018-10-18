import hashlib
import math
import random

from core.modules import secret_sharing as ss, threshold_rsa as tr, \
    misc


# share distribution
def split_verify_shares(d, m, l, k):
    coefficient_lst, shares_lst = (ss.split_secret(l, k, m, d))
    print("\nEvaluated polynomial: ", shares_lst)

    node_share_dict = {}
    while True:
        if len(node_share_dict) == k:
            break
        i = random.randint(1, l)
        if i not in node_share_dict:
            node_share_dict[i] = shares_lst[i - 1]

    return node_share_dict


# Shoup's Threshold RSA

b_rsa = int(input("\nEnter bit size for RSA primes: "))
p_ = misc.generateLargePrime(b_rsa)
while True:
    q_ = misc.generateLargePrime(b_rsa)
    if q_ != p_:
        break
p_rsa = 2 * p_ + 1
q_rsa = 2 * q_ + 1
n = p_rsa * q_rsa
m = p_ * q_
e = 65537
d = misc.multiplicative_inverse(e, m)
print("p:", p_rsa)
print("q:", q_rsa)
print("p':", p_)
print("q':", q_)
print("Public key (n,e):", n, e)
print("Private key (d):", d)
print("m:", m)

# k out of l
l = int(input("\nEnter total nodes: "))
k = int(input("Enter threshold: "))
delta = math.factorial(l)
print("delta:", delta)

msg = input("\nEnter message to be signed: ")
digest = hashlib.sha1(msg.encode("utf-8")).hexdigest()
digest = int(digest, 16)
node_share_dict = split_verify_shares(d, m, l, k)
sig_orig = misc.square_and_multiply(digest, d, n)
dec_orig = misc.square_and_multiply(sig_orig, e, n)
threshold_sig = tr.compute_threhold_sig(node_share_dict, digest, delta, n, e)
dec = misc.square_and_multiply(threshold_sig, e, n)
print(sig_orig, dec_orig, threshold_sig, dec)
