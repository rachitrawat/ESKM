import random

from core.modules import secret_sharing as ss, lagrange_interpolation as li

debug = True
n = int(input("Enter n: "))
k = int(input("Enter k: "))
p = int(input("Enter p: "))
s = int(input("Enter s: "))

f_eval_lst = (ss.split_secret(n, k, p, s, debug))

print("Evaluated polynomial: ", f_eval_lst)

# select k random nodes
# dict[node_i]= f(i)
dict = {}
while True:
    if len(dict) == k:
        break
    i = random.randint(1, n)
    if i not in dict:
        dict[i] = f_eval_lst[i - 1]

secret = li.reconstruct_secret(dict, p, debug)
print("\nReconstructed Secret: ", secret)
