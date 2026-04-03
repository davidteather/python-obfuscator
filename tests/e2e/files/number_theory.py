"""Number theory: primes, factorisation, modular arithmetic, combinatorics."""


def sieve(limit):
    """Return all primes up to limit via Sieve of Eratosthenes."""
    if limit < 2:
        return []
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            is_prime[i * i :: i] = bytearray(len(is_prime[i * i :: i]))
    return [i for i in range(2, limit + 1) if is_prime[i]]


def factorize(n):
    """Return prime factorisation as list (with repetition)."""
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    return factors


def gcd(a, b):
    while b:
        a, b = b, a % b
    return a


def lcm(a, b):
    return a * b // gcd(a, b)


def extended_gcd(a, b):
    """Return (g, x, y) such that a*x + b*y = g = gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_inverse(a, m):
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        return None
    return x % m


def pow_mod(base, exp, mod):
    """Fast modular exponentiation."""
    result = 1
    base %= mod
    while exp > 0:
        if exp % 2 == 1:
            result = result * base % mod
        exp //= 2
        base = base * base % mod
    return result


def miller_rabin(n, witnesses=None):
    """Deterministic Miller-Rabin for n < 3_215_031_751."""
    if n < 2:
        return False
    if n in (2, 3, 5, 7):
        return True
    if n % 2 == 0:
        return False
    d, r = n - 1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for a in witnesses or [2, 3, 5, 7]:
        if a >= n:
            continue
        x = pow_mod(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow_mod(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def goldbach(n):
    """Express even n >= 4 as sum of two primes (Goldbach)."""
    primes = set(sieve(n))
    for p in sorted(primes):
        if n - p in primes:
            return p, n - p
    return None


def totient(n):
    """Euler's totient function phi(n)."""
    result = n
    p = 2
    temp = n
    while p * p <= temp:
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
        p += 1
    if temp > 1:
        result -= result // temp
    return result


def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def choose(n, k):
    if k > n:
        return 0
    k = min(k, n - k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


# ── outputs ───────────────────────────────────────────────────────────────────

primes_100 = sieve(100)
print(f"primes<=100: {len(primes_100)} primes, sum={sum(primes_100)}")
print(f"first 10: {primes_100[:10]}")

for n in [12, 360, 1024, 9973]:
    facs = factorize(n)
    product = 1
    for f in facs:
        product *= f
    print(f"factors({n}): {facs}  product={product}")

pairs = [(12, 8), (100, 75), (17, 5), (1001, 77)]
for a, b in pairs:
    print(f"gcd({a},{b})={gcd(a,b)}  lcm={lcm(a,b)}")

print("miller-rabin:")
for n in [2, 17, 100, 997, 998, 7919]:
    result = miller_rabin(n)
    naive = n in set(sieve(8000))
    match = "OK" if result == naive else "FAIL"
    print(f"  {n}: {result}  {match}")

print("goldbach:")
for n in [28, 100, 200]:
    p, q = goldbach(n)
    print(f"  {n} = {p} + {q}")

print("totient:")
for n in [1, 6, 10, 36, 100]:
    print(f"  phi({n}) = {totient(n)}")

print("mod-inverse:")
for a, m in [(3, 7), (10, 17), (6, 35)]:
    inv = mod_inverse(a, m)
    print(f"  {a}^-1 mod {m} = {inv}")

print("binomial:")
for n, k in [(5, 2), (10, 3), (20, 10)]:
    print(f"  C({n},{k}) = {choose(n,k)}")

print(f"10! = {factorial(10)}")
print(f"pow_mod(2,100,1000000007) = {pow_mod(2, 100, 1000000007)}")
