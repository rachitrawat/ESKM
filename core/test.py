import random

from core.modules import secret_sharing as ss, lagrange_interpolation as li, verify_share as vs, misc

n = int(input("Enter total nodes: "))
k = int(input("Enter threshold: "))
s = int(input("Enter secret: "))
# secret bit size
# s is in 0...p-1
s_size = len("{0:b}".format(s))
# generate prime p st 2 * p + 1 is also a prime
# p is s_size + 1 bits
p = misc.generateLargePrime(s_size + 1)
# q is a prime such that p divides q-1
q = (2 * p) + 1
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

# share reconstruction

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