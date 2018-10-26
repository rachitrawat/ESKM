import random

from core.modules import secret_sharing as ss, lagrange_interpolation as li, share_verification as vs, misc


def split_verify_reconstruct(s):
    n = int(input("\nEnter total nodes: "))
    k = int(input("Enter threshold: "))
    # s = int(input("Enter secret: "))
    # secret bit size
    # s is in 0...p-1
    s_size = len("{0:b}".format(s))
    # q is a safe prime
    q = misc.generate_safe_prime(s_size + 1)
    p = (q - 1) // 2
    print("Generated primes:", p, q)
    # generator
    g = misc.find_primitive_root(q)
    # set g as quadratic residue mod q
    g = misc.square_and_multiply(g, 2, q)
    print("Generator:", g)

    # share distribution

    coeff_lst, f_eval_lst = (ss.split_secret(n, k, p, s))
    print("\nEvaluated polynomial: ", f_eval_lst)

    # share verification

    publish_lst = []
    for element in coeff_lst:
        publish_lst.append(misc.square_and_multiply(g, element, q))

    print("\nPublished info for verification: ", publish_lst)
    for i in range(1, n + 1):
        if not vs.verify_share(i, misc.square_and_multiply(g, f_eval_lst[i - 1], q), publish_lst, q):
            print("\nNode %s: share verification has failed!" % i)
            exit(1)

    print("\nAll nodes have verified their shares!")

    # secret reconstruction

    # select k random nodes
    # dict[node_i]= f(i)
    dict = {}
    while True:
        if len(dict) == k:
            break
        i = random.randint(1, n)
        if i not in dict:
            dict[i] = f_eval_lst[i - 1]

    secret = li.reconstruct_secret(dict, p)
    print("\nReconstructed Secret: ", secret)


# threshold RSA

b_rsa = int(input("\nEnter bit size for RSA primes: "))
p_rsa = misc.generate_safe_prime(b_rsa)
while True:
    q_rsa = misc.generate_safe_prime(b_rsa)
    if q_rsa != p_rsa:
        break
totient_rsa = (p_rsa - 1) * (q_rsa - 1)
n_rsa = p_rsa * q_rsa
print("Generated n,p,q,totient:", n_rsa, p_rsa, q_rsa, totient_rsa)
e = 65537
d = misc.multiplicative_inverse(e, totient_rsa)
print("Public key (n,e):", n_rsa, e)
print("Private key (d):", d)

split_verify_reconstruct(d)
