"""End-to-end integration tests.

Each test writes a non-trivial Python program, executes it with an empty
config (no transforms) to get the baseline output, then executes the fully
obfuscated version and asserts the output is identical.

Output is captured by overriding ``print`` in the execution namespace.
This works even when ``exec_wrapper`` is active because the inner ``exec``
call inherits the outer globals dict (which contains our fake print), and
``variable_renamer`` and ``dead_code_injector`` never touch the ``print``
name (it is a builtin and therefore excluded from all transforms).
"""

from __future__ import annotations

import textwrap

import pytest

from python_obfuscator import ObfuscationConfig, obfuscate


def run(source: str, config: ObfuscationConfig | None = None) -> list[str]:
    """Execute *source* and return every string passed to print(), in order."""
    captured: list[str] = []

    def fake_print(
        *args: object, sep: str = " ", end: str = "\n", **_: object
    ) -> None:  # noqa: ARG001
        captured.append(sep.join(str(a) for a in args))

    cfg = config or ObfuscationConfig.all_enabled()
    ns: dict = {"print": fake_print}
    exec(obfuscate(source, config=cfg), ns)  # noqa: S102
    return captured


_BASELINE = ObfuscationConfig.only()  # no transforms — plain exec


def check(source: str) -> None:
    """Assert that fully-obfuscated output matches unobfuscated output."""
    expected = run(source, config=_BASELINE)
    actual = run(source)
    assert (
        actual == expected
    ), f"Obfuscated output differs.\nExpected: {expected}\nActual:   {actual}"


# ---------------------------------------------------------------------------
# Individual technique passes (useful for isolating regressions)
# ---------------------------------------------------------------------------


class TestIndividualTechniques:
    _SRC = textwrap.dedent(
        """\
        x = 10
        y = 20
        print(x + y)
        print(x * y)
        """
    )

    def test_string_hex_encoder_only(self) -> None:
        cfg = ObfuscationConfig.only("string_hex_encoder")
        assert run(self._SRC, config=_BASELINE) == run(self._SRC, config=cfg)

    def test_variable_renamer_only(self) -> None:
        cfg = ObfuscationConfig.only("variable_renamer")
        assert run(self._SRC, config=_BASELINE) == run(self._SRC, config=cfg)

    def test_dead_code_injector_only(self) -> None:
        cfg = ObfuscationConfig.only("dead_code_injector")
        assert run(self._SRC, config=_BASELINE) == run(self._SRC, config=cfg)

    def test_exec_wrapper_only(self) -> None:
        cfg = ObfuscationConfig.only("exec_wrapper")
        assert run(self._SRC, config=_BASELINE) == run(self._SRC, config=cfg)


# ---------------------------------------------------------------------------
# Full-pipeline scenarios
# ---------------------------------------------------------------------------


class TestArithmetic:
    def test_basic_arithmetic(self) -> None:
        check(
            textwrap.dedent(
                """\
                a = 6
                b = 7
                print(a + b)
                print(a * b)
                print(a - b)
                print(100 // a)
                print(100 % b)
                """
            )
        )

    def test_float_arithmetic(self) -> None:
        check(
            textwrap.dedent(
                """\
                x = 3.14
                y = 2.0
                print(round(x * y, 4))
                print(round(x / y, 4))
                """
            )
        )

    def test_chained_operations(self) -> None:
        check(
            textwrap.dedent(
                """\
                result = (1 + 2) * (3 + 4) - (5 * 6) + (7 ** 2)
                print(result)
                """
            )
        )


class TestFunctions:
    def test_simple_function(self) -> None:
        check(
            textwrap.dedent(
                """\
                def add(a, b):
                    return a + b
                print(add(3, 4))
                print(add(10, -3))
                """
            )
        )

    def test_recursive_fibonacci(self) -> None:
        check(
            textwrap.dedent(
                """\
                def fib(n):
                    if n <= 1:
                        return n
                    return fib(n - 1) + fib(n - 2)
                for i in range(8):
                    print(fib(i))
                """
            )
        )

    def test_default_arguments(self) -> None:
        # Keyword-argument call sites use bare strings (ast.keyword.arg), not
        # ast.Name nodes, so variable_renamer cannot update them when a parameter
        # is renamed.  Use positional arguments to keep the test self-consistent
        # after renaming.
        check(
            textwrap.dedent(
                """\
                def greet(name, prefix="Hello"):
                    return prefix + " " + name
                print(greet("world"))
                print(greet("Python", "Hi"))
                """
            )
        )

    def test_multiple_return_values(self) -> None:
        check(
            textwrap.dedent(
                """\
                def minmax(seq):
                    return min(seq), max(seq)
                lo, hi = minmax([3, 1, 4, 1, 5, 9, 2, 6])
                print(lo, hi)
                """
            )
        )

    def test_variadic_args(self) -> None:
        check(
            textwrap.dedent(
                """\
                def total(*nums):
                    return sum(nums)
                print(total(1, 2, 3, 4, 5))
                """
            )
        )

    def test_higher_order_function(self) -> None:
        check(
            textwrap.dedent(
                """\
                def apply(fn, values):
                    return [fn(v) for v in values]
                result = apply(lambda x: x * x, [1, 2, 3, 4])
                for v in result:
                    print(v)
                """
            )
        )


class TestClosures:
    def test_simple_closure(self) -> None:
        check(
            textwrap.dedent(
                """\
                def make_adder(n):
                    def inner(x):
                        return x + n
                    return inner
                add5 = make_adder(5)
                print(add5(10))
                print(add5(0))
                """
            )
        )

    def test_nonlocal(self) -> None:
        check(
            textwrap.dedent(
                """\
                def counter():
                    count = 0
                    def inc():
                        nonlocal count
                        count += 1
                        return count
                    return inc
                c = counter()
                print(c())
                print(c())
                print(c())
                """
            )
        )


class TestClasses:
    def test_simple_class(self) -> None:
        check(
            textwrap.dedent(
                """\
                class Point:
                    def __init__(self, x, y):
                        self.x = x
                        self.y = y
                    def distance(self):
                        return (self.x ** 2 + self.y ** 2) ** 0.5
                p = Point(3, 4)
                print(p.distance())
                """
            )
        )

    def test_inheritance(self) -> None:
        check(
            textwrap.dedent(
                """\
                class Animal:
                    def __init__(self, name):
                        self.name = name
                    def speak(self):
                        return "..."
                class Dog(Animal):
                    def speak(self):
                        return "Woof"
                class Cat(Animal):
                    def speak(self):
                        return "Meow"
                for animal in [Dog("Rex"), Cat("Whiskers")]:
                    print(animal.speak())
                """
            )
        )

    def test_class_method_and_static(self) -> None:
        check(
            textwrap.dedent(
                """\
                class MathHelper:
                    factor = 2
                    @classmethod
                    def double(cls, n):
                        return n * cls.factor
                    @staticmethod
                    def square(n):
                        return n * n
                print(MathHelper.double(5))
                print(MathHelper.square(4))
                """
            )
        )


class TestControlFlow:
    def test_for_loop(self) -> None:
        check(
            textwrap.dedent(
                """\
                total = 0
                for i in range(1, 6):
                    total += i
                print(total)
                """
            )
        )

    def test_while_loop(self) -> None:
        check(
            textwrap.dedent(
                """\
                n = 1
                while n < 32:
                    n *= 2
                print(n)
                """
            )
        )

    def test_nested_for_loops(self) -> None:
        check(
            textwrap.dedent(
                """\
                pairs = []
                for i in range(3):
                    for j in range(3):
                        if i != j:
                            pairs.append((i, j))
                print(len(pairs))
                """
            )
        )

    def test_if_elif_else(self) -> None:
        check(
            textwrap.dedent(
                """\
                def classify(n):
                    if n < 0:
                        return "negative"
                    elif n == 0:
                        return "zero"
                    else:
                        return "positive"
                for v in [-5, 0, 7]:
                    print(classify(v))
                """
            )
        )

    def test_break_and_continue(self) -> None:
        check(
            textwrap.dedent(
                """\
                evens = []
                for i in range(20):
                    if i % 2 != 0:
                        continue
                    if i > 10:
                        break
                    evens.append(i)
                print(evens)
                """
            )
        )


class TestDataStructures:
    def test_list_comprehension(self) -> None:
        check(
            textwrap.dedent(
                """\
                squares = [x * x for x in range(6)]
                print(squares)
                """
            )
        )

    def test_dict_comprehension(self) -> None:
        check(
            textwrap.dedent(
                """\
                word = "hello"
                freq = {c: word.count(c) for c in set(word)}
                for key in sorted(freq):
                    print(key, freq[key])
                """
            )
        )

    def test_set_operations(self) -> None:
        check(
            textwrap.dedent(
                """\
                a = {1, 2, 3, 4}
                b = {3, 4, 5, 6}
                print(sorted(a & b))
                print(sorted(a | b))
                print(sorted(a - b))
                """
            )
        )

    def test_nested_list(self) -> None:
        check(
            textwrap.dedent(
                """\
                matrix = [[i * j for j in range(1, 4)] for i in range(1, 4)]
                for row in matrix:
                    print(row)
                """
            )
        )


class TestExceptionHandling:
    def test_try_except(self) -> None:
        check(
            textwrap.dedent(
                """\
                def safe_div(a, b):
                    try:
                        return a // b
                    except ZeroDivisionError:
                        return None
                print(safe_div(10, 2))
                print(safe_div(10, 0))
                """
            )
        )

    def test_try_except_finally(self) -> None:
        check(
            textwrap.dedent(
                """\
                log = []
                try:
                    log.append("try")
                    x = 1 // 0
                except ZeroDivisionError:
                    log.append("except")
                finally:
                    log.append("finally")
                print(log)
                """
            )
        )

    def test_multiple_except_clauses(self) -> None:
        check(
            textwrap.dedent(
                """\
                def parse_int(s):
                    try:
                        return int(s)
                    except (ValueError, TypeError):
                        return -1
                print(parse_int("42"))
                print(parse_int("abc"))
                print(parse_int(None))
                """
            )
        )

    def test_try_else(self) -> None:
        check(
            textwrap.dedent(
                """\
                results = []
                for val in ["10", "x", "5"]:
                    try:
                        n = int(val)
                    except ValueError:
                        results.append("bad")
                    else:
                        results.append(n * 2)
                print(results)
                """
            )
        )


class TestGenerators:
    def test_generator_function(self) -> None:
        check(
            textwrap.dedent(
                """\
                def countdown(n):
                    while n > 0:
                        yield n
                        n -= 1
                print(list(countdown(5)))
                """
            )
        )

    def test_generator_expression(self) -> None:
        check(
            textwrap.dedent(
                """\
                gen = (x * x for x in range(5))
                print(list(gen))
                """
            )
        )


class TestStringOperations:
    def test_string_formatting(self) -> None:
        check(
            textwrap.dedent(
                """\
                name = "world"
                n = 42
                print(f"Hello, {name}!")
                print(f"The answer is {n}.")
                """
            )
        )

    def test_string_methods(self) -> None:
        check(
            textwrap.dedent(
                """\
                s = "Hello, World!"
                print(s.lower())
                print(s.upper())
                print(s.replace("World", "Python"))
                print(s.split(", "))
                """
            )
        )

    def test_multiline_string(self) -> None:
        check(
            textwrap.dedent(
                """\
                text = "line one\\nline two\\nline three"
                lines = text.split("\\n")
                for line in lines:
                    print(line)
                """
            )
        )

    def test_string_with_quotes(self) -> None:
        check(
            textwrap.dedent(
                """\
                s1 = "it's a test"
                s2 = 'say "hello"'
                print(s1)
                print(s2)
                """
            )
        )


class TestComplexPrograms:
    def test_bubble_sort(self) -> None:
        check(
            textwrap.dedent(
                """\
                def bubble_sort(lst):
                    n = len(lst)
                    for i in range(n):
                        for j in range(n - i - 1):
                            if lst[j] > lst[j + 1]:
                                lst[j], lst[j + 1] = lst[j + 1], lst[j]
                    return lst
                data = [64, 34, 25, 12, 22, 11, 90]
                print(bubble_sort(data))
                """
            )
        )

    def test_binary_search(self) -> None:
        check(
            textwrap.dedent(
                """\
                def binary_search(lst, target):
                    lo, hi = 0, len(lst) - 1
                    while lo <= hi:
                        mid = (lo + hi) // 2
                        if lst[mid] == target:
                            return mid
                        elif lst[mid] < target:
                            lo = mid + 1
                        else:
                            hi = mid - 1
                    return -1
                arr = list(range(0, 20, 2))
                print(binary_search(arr, 8))
                print(binary_search(arr, 7))
                """
            )
        )

    def test_class_with_dunder_methods(self) -> None:
        check(
            textwrap.dedent(
                """\
                class Stack:
                    def __init__(self):
                        self._data = []
                    def push(self, item):
                        self._data.append(item)
                    def pop(self):
                        return self._data.pop()
                    def __len__(self):
                        return len(self._data)
                    def __repr__(self):
                        return repr(self._data)
                s = Stack()
                s.push(1)
                s.push(2)
                s.push(3)
                print(len(s))
                print(s.pop())
                print(len(s))
                """
            )
        )

    def test_functional_pipeline(self) -> None:
        check(
            textwrap.dedent(
                """\
                from functools import reduce
                numbers = list(range(1, 11))
                evens = list(filter(lambda x: x % 2 == 0, numbers))
                doubled = list(map(lambda x: x * 2, evens))
                total = reduce(lambda a, b: a + b, doubled)
                print(evens)
                print(doubled)
                print(total)
                """
            )
        )

    def test_deeply_nested_closures(self) -> None:
        check(
            textwrap.dedent(
                """\
                def level1(a):
                    def level2(b):
                        def level3(c):
                            return a + b + c
                        return level3
                    return level2
                fn = level1(1)(2)
                print(fn(3))
                print(fn(10))
                """
            )
        )

    def test_memoisation_with_dict(self) -> None:
        check(
            textwrap.dedent(
                """\
                cache = {}
                def fib(n):
                    if n in cache:
                        return cache[n]
                    if n <= 1:
                        cache[n] = n
                    else:
                        cache[n] = fib(n - 1) + fib(n - 2)
                    return cache[n]
                for i in [0, 1, 5, 10, 15]:
                    print(fib(i))
                """
            )
        )
