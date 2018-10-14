from random import randint
from numpy.polynomial.polynomial import polyval

n = int(input("Enter n: "))
k = int(input("Enter k: "))

print("%s out of %s secret sharing. " % (k, n))

p = 11
s = 3

coeff_list = [s]

# Choose k-1 degree elements in Zp
for i in range(1, k):
    coeff_list.append(randint(0, p - 1))

print(coeff_list)

for i in range(1, n + 1):
    print(i, (int(polyval(i, coeff_list))) % p)
