import hashlib
import math
import random

from core.modules import secret_sharing as ss, threshold_rsa as tr, \
    misc, share_verification as sv


# share distribution
def split_verify_shares(d, m, n, l, k, p, q):
    coefficient_lst, shares_lst = (ss.split_secret(l, k, m, d))
    print("\nEvaluated polynomial: ", shares_lst)

    # q = n
    # g = 3

    # TODO
    # n=pq
    # find g in Zn*
    # 1. find g_p in Zp*
    g_p = misc.find_primitive_root(p)
    # 2. find g_q in Zq*
    g_q = misc.find_primitive_root(q)
    # 3. Combine using CRT
    g = misc.crt([g_p, g_q], [p, q])

    # share verification

    publish_lst = []
    for element in coefficient_lst:
        publish_lst.append(misc.square_and_multiply(g, element, n))

    print("\nPublished info for verification: ", publish_lst)

    for i in range(1, l + 1):
        if not sv.verify_share(i, misc.square_and_multiply(g, shares_lst[i - 1], n), publish_lst, n):
            print("\nNode %s: share verification has failed!" % i)
            exit(1)

    print("\nAll nodes have verified their shares!")

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
node_share_dict = split_verify_shares(d, m, n, l, k, p_rsa, q_rsa)
threshold_sig = tr.compute_threhold_sig(node_share_dict, digest, delta, n, e)
dec = misc.square_and_multiply(threshold_sig, e, n)
print("\nThresh. Sig and Dec:", threshold_sig, dec)
print("Sig. match: ", dec == digest % n)
