"""Functional programming patterns: higher-order functions, generators, lazy pipelines."""

from functools import reduce

# ── Core combinators ──────────────────────────────────────────────────────────


def compose(*fns):
    """Right-to-left function composition."""

    def composed(x):
        for fn in reversed(fns):
            x = fn(x)
        return x

    return composed


def pipe(*fns):
    """Left-to-right function composition."""
    return compose(*reversed(fns))


def curry(fn):
    """Simple two-argument currying."""

    def curried(a):
        def inner(b):
            return fn(a, b)

        return inner

    return curried


def memoize(fn):
    cache = {}

    def wrapper(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]

    return wrapper


def trampoline(fn):
    """Run a thunk-returning function iteratively to avoid stack overflow."""

    def run(*args):
        result = fn(*args)
        while callable(result):
            result = result()
        return result

    return run


# ── Lazy sequences ─────────────────────────────────────────────────────────────


def take(n, iterable):
    result = []
    for i, item in enumerate(iterable):
        if i >= n:
            break
        result.append(item)
    return result


def drop(n, iterable):
    it = iter(iterable)
    for _ in range(n):
        next(it, None)
    return list(it)


def naturals(start=0):
    n = start
    while True:
        yield n
        n += 1


def fibs():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def primes_gen():
    """Infinite prime generator using a sieve dict."""
    composites = {}
    n = 2
    while True:
        if n not in composites:
            yield n
            composites[n * n] = [n]
        else:
            for p in composites[n]:
                composites.setdefault(n + p, []).append(p)
            del composites[n]
        n += 1


def scan(fn, iterable, initial=None):
    """Running accumulation (like Haskell's scanl)."""
    acc = initial
    result = [] if initial is None else [initial]
    for item in iterable:
        acc = fn(acc, item) if acc is not None else item
        result.append(acc)
    return result


def zip_with(fn, *iterables):
    return [fn(*args) for args in zip(*iterables)]


def flatten(nested, depth=1):
    result = []
    for item in nested:
        if isinstance(item, (list, tuple)) and depth > 0:
            result.extend(flatten(item, depth - 1))
        else:
            result.append(item)
    return result


def group_by(fn, iterable):
    groups = {}
    for item in iterable:
        key = fn(item)
        groups.setdefault(key, []).append(item)
    return groups


def partition(pred, iterable):
    yes, no = [], []
    for item in iterable:
        (yes if pred(item) else no).append(item)
    return yes, no


# ── Memoized recursive algorithms ─────────────────────────────────────────────


@memoize
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


@memoize
def catalan(n):
    if n == 0:
        return 1
    return sum(catalan(i) * catalan(n - 1 - i) for i in range(n))


# ── Outputs ────────────────────────────────────────────────────────────────────

double = curry(lambda a, b: a * b)(2)
add10 = curry(lambda a, b: a + b)(10)


def square(x):
    return x * x


pipeline = pipe(double, add10, square)
inputs = [1, 2, 3, 4, 5]
print("pipeline results:", [pipeline(x) for x in inputs])

composed = compose(str, square, double)
print("composed:", [composed(x) for x in inputs])

fib_list = take(15, fibs())
print("fibs:", fib_list)
print("fib(30):", fib(30))

prime_list = take(20, primes_gen())
print("primes:", prime_list)
print("50th prime:", take(50, primes_gen())[-1])

evens, odds = partition(lambda x: x % 2 == 0, range(20))
print("evens:", evens)
print("odds:", odds)

by_mod = group_by(lambda x: x % 3, range(15))
for k in sorted(by_mod):
    print(f"mod3={k}: {by_mod[k]}")

running_sum = scan(lambda a, b: a + b, range(1, 11))
print("running sum:", running_sum)

pairs = zip_with(lambda a, b: a * b, range(1, 6), range(6, 11))
print("zip_with mul:", pairs)

nested = [[1, [2, 3]], [4, [5, [6]]]]
print("flatten(depth=1):", flatten(nested, 1))
print("flatten(depth=2):", flatten(nested, 2))

catalan_list = [catalan(n) for n in range(10)]
print("catalan:", catalan_list)

# Transducer-style pipeline using reduce
data = list(range(1, 21))
result = reduce(
    lambda acc, x: acc + [x * x] if x % 2 == 0 else acc,
    data,
    [],
)
print("squares of evens:", result)
print("sum:", sum(result))

# Triangle numbers via scan over a finite range
triangles = scan(lambda a, b: a + b, range(1, 12))
print("triangle numbers:", triangles)
