from functools import reduce

p = 11


def lambda_eval(i, n, p, x=0):
    num = []
    den = []
    for element in n:
        if element != i:
            num.append(x - element)
            den.append(i - element)

    eval_num = reduce(lambda x, y: x * y, num)
    eval_den = reduce(lambda x, y: x * y, den)

    if eval_den < 0:
        eval_den = p - abs(eval_den)

    return (eval_num * mulinv(eval_den, p)) % p


# return (g, x, y) a*x + b*y = gcd(x, y)
def egcd(a, b):
    if a == 0:
        return b, 0, 1
    else:
        g, x, y = egcd(b % a, a)
        return g, y - (b // a) * x, x


# x = mulinv(b) mod n, (x * b) % n == 1
def mulinv(b, n):
    g, x, _ = egcd(b, n)
    if g == 1:
        return x % n


node = [1, 3, 5]
f = [6, 2, 3]
sum = 0

for idx, val in enumerate(node):
    sum += lambda_eval(val, node, p) * f[idx]
    sum %= p

print(sum)
