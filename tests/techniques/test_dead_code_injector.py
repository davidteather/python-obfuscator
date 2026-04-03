"""Tests for DeadCodeInjector."""

import ast
import random
import textwrap

import pytest

from python_obfuscator.techniques.ast_transforms.dead_code_injector import (
    DeadCodeInjector,
    InjectionParams,
    _interleave,
)
from python_obfuscator.techniques.registry import all_technique_names

# Small params so tests run quickly and counts are predictable.
_FAST = InjectionParams(stmts_per_scope_min=2, stmts_per_scope_max=4)


def _apply(
    source: str,
    rng: random.Random | None = None,
    params: InjectionParams | None = None,
) -> str:
    tree = ast.parse(source)
    return ast.unparse(DeadCodeInjector(rng=rng, params=params).apply(tree))


def _all_assigns(source: str) -> list[str]:
    """Return every assigned name in *source* (module-wide walk)."""
    return [
        node.targets[0].id
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
    ]


class TestInterleave:
    def test_result_is_sum_of_lengths(self) -> None:
        orig = [ast.parse("x = 1").body[0], ast.parse("y = 2").body[0]]
        inj = [ast.parse("j = 0").body[0]]
        assert len(_interleave(orig, inj, random.Random(0))) == 3

    def test_empty_injected_returns_copy(self) -> None:
        orig = [ast.parse("x = 1").body[0]]
        result = _interleave(orig, [], random.Random(0))
        assert len(result) == 1

    def test_empty_original_receives_injected(self) -> None:
        inj = [ast.parse("j = 0").body[0]]
        assert len(_interleave([], inj, random.Random(0))) == 1

    def test_does_not_mutate_original(self) -> None:
        orig = [ast.parse("x = 1").body[0]]
        _interleave(orig, [ast.parse("j = 0").body[0]], random.Random(0))
        assert len(orig) == 1

    def test_seeded_order_is_reproducible(self) -> None:
        orig = [ast.parse("x = 1").body[0], ast.parse("y = 2").body[0]]
        inj = [ast.parse(f"j{i} = {i}").body[0] for i in range(5)]
        r1 = [ast.unparse(n) for n in _interleave(orig, inj[:], random.Random(7))]
        r2 = [ast.unparse(n) for n in _interleave(orig, inj[:], random.Random(7))]
        assert r1 == r2


class TestDeadCodeInjector:
    def test_is_registered(self) -> None:
        assert "dead_code_injector" in all_technique_names()

    def test_output_is_valid_python(self) -> None:
        ast.parse(_apply("x = 1", params=_FAST))

    def test_output_has_more_assignments_than_input(self) -> None:
        result = _apply("x = 1\ny = 2\n", rng=random.Random(0), params=_FAST)
        assert len(_all_assigns(result)) > 2

    def test_seeded_rng_produces_identical_output(self) -> None:
        r1 = _apply("x = 1", rng=random.Random(42), params=_FAST)
        r2 = _apply("x = 1", rng=random.Random(42), params=_FAST)
        assert r1 == r2

    def test_different_seeds_produce_different_output(self) -> None:
        r1 = _apply("x = 1", rng=random.Random(1), params=_FAST)
        r2 = _apply("x = 1", rng=random.Random(2), params=_FAST)
        assert r1 != r2

    def test_original_variable_not_clobbered(self) -> None:
        source = "sentinel_val = 999\n"
        ns: dict = {}
        exec(_apply(source, rng=random.Random(0), params=_FAST), ns)
        assert ns["sentinel_val"] == 999

    def test_builtin_not_shadowed(self) -> None:
        source = "result = len([1, 2, 3])\n"
        ns: dict = {}
        exec(_apply(source, rng=random.Random(0), params=_FAST), ns)
        assert ns["result"] == 3

    def test_imported_name_not_shadowed(self) -> None:
        source = "import os\npath = os.path.sep\n"
        ns: dict = {}
        exec(_apply(source, rng=random.Random(0), params=_FAST), ns)
        assert isinstance(ns["path"], str)

    def test_function_behavior_preserved(self) -> None:
        source = textwrap.dedent(
            """\
            def add(a, b):
                return a + b
            result = add(3, 4)
            """
        )
        ns: dict = {}
        exec(_apply(source, rng=random.Random(7), params=_FAST), ns)
        assert ns["result"] == 7

    def test_junk_names_are_valid_identifiers(self) -> None:
        for name in _all_assigns(_apply("x = 1", rng=random.Random(0), params=_FAST)):
            assert name.isidentifier(), f"{name!r} is not a valid identifier"

    def test_junk_names_globally_unique(self) -> None:
        result = _apply("x = 1", rng=random.Random(0), params=_FAST)
        names = _all_assigns(result)
        assert len(names) == len(set(names))

    def test_apply_returns_module(self) -> None:
        tree = ast.parse("x = 1")
        assert isinstance(
            DeadCodeInjector(rng=random.Random(0)).apply(tree), ast.Module
        )

    def test_apply_produces_compilable_tree(self) -> None:
        tree = ast.parse("x = 1\ny = 2")
        compile(DeadCodeInjector(rng=random.Random(0)).apply(tree), "<string>", "exec")

    def test_max_attempts_guard_with_all_names_colliding(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from python_obfuscator.helpers.variable_name_generator import (
            VariableNameGenerator,
        )

        monkeypatch.setattr(VariableNameGenerator, "get_random", lambda self, id: "x")
        tree = ast.parse("x = 1")
        result = DeadCodeInjector(rng=random.Random(0)).apply(tree)
        assert isinstance(result, ast.Module)
        ns: dict = {}
        exec(ast.unparse(result), ns)
        assert ns["x"] == 1

    def test_zero_stmts_per_scope_produces_no_junk(self) -> None:
        # Covers the for-loop-exhausted-naturally branch (count * 10 = 0
        # iterations so the loop body never executes).
        params = InjectionParams(stmts_per_scope_min=0, stmts_per_scope_max=0)
        source = "x = 1\n"
        result = _apply(source, rng=random.Random(0), params=params)
        # No new Assign nodes should have been injected
        assigns = _all_assigns(result)
        assert assigns == ["x"]


class TestRecursiveInjection:
    """Verify that injection happens inside nested scopes."""

    def test_injects_into_function_body(self) -> None:
        source = textwrap.dedent(
            """\
            def foo():
                return 1
            """
        )
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        func = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        assigns_in_func = [
            n
            for n in ast.walk(ast.Module(body=func.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(assigns_in_func) > 0

    def test_injects_into_class_body(self) -> None:
        source = textwrap.dedent(
            """\
            class Foo:
                x = 1
            """
        )
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        assigns = [
            n
            for n in ast.walk(ast.Module(body=cls.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(assigns) > 1  # original 'x = 1' plus junk

    def test_injects_into_if_body(self) -> None:
        source = "if True:\n    x = 1\n"
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        if_node = next(n for n in ast.walk(tree) if isinstance(n, ast.If))
        assigns = [
            n
            for n in ast.walk(ast.Module(body=if_node.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(assigns) > 1

    def test_injects_into_for_body(self) -> None:
        source = "total = 0\nfor i in range(3):\n    total += i\n"
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        for_node = next(n for n in ast.walk(tree) if isinstance(n, ast.For))
        assigns = [
            n
            for n in ast.walk(ast.Module(body=for_node.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(assigns) > 0

    def test_injects_into_for_orelse(self) -> None:
        source = textwrap.dedent(
            """\
            for i in range(3):
                pass
            else:
                found = True
            """
        )
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        for_node = next(n for n in ast.walk(tree) if isinstance(n, ast.For))
        assert for_node.orelse, "for/else should be preserved"
        assigns = [
            n
            for n in ast.walk(ast.Module(body=for_node.orelse, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        # orelse has 'found = True' plus injected junk
        assert len(assigns) > 1

    def test_injects_into_while_body(self) -> None:
        source = "i = 0\nwhile i < 1:\n    i += 1\n"
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        while_node = next(n for n in ast.walk(tree) if isinstance(n, ast.While))
        assigns = [
            n
            for n in ast.walk(ast.Module(body=while_node.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(assigns) > 0

    def test_injects_into_try_body(self) -> None:
        source = textwrap.dedent(
            """\
            try:
                x = 1
            except Exception:
                pass
            """
        )
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        try_node = next(n for n in ast.walk(tree) if isinstance(n, ast.Try))
        assigns = [
            n
            for n in ast.walk(ast.Module(body=try_node.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(assigns) > 1

    def test_injects_into_except_handler(self) -> None:
        source = textwrap.dedent(
            """\
            try:
                x = 1
            except Exception:
                pass
            """
        )
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        try_node = next(n for n in ast.walk(tree) if isinstance(n, ast.Try))
        handler_assigns = [
            n
            for h in try_node.handlers
            for n in ast.walk(ast.Module(body=h.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(handler_assigns) > 0

    def test_injects_into_with_body(self) -> None:
        source = textwrap.dedent(
            """\
            import contextlib
            with contextlib.suppress(Exception):
                x = 1
            """
        )
        result = _apply(source, rng=random.Random(0), params=_FAST)
        tree = ast.parse(result)
        with_node = next(n for n in ast.walk(tree) if isinstance(n, ast.With))
        assigns = [
            n
            for n in ast.walk(ast.Module(body=with_node.body, type_ignores=[]))
            if isinstance(n, ast.Assign)
        ]
        assert len(assigns) > 1

    def test_nested_function_behavior_preserved(self) -> None:
        source = textwrap.dedent(
            """\
            def outer(x):
                def inner(y):
                    return x + y
                return inner
            result = outer(3)(4)
            """
        )
        ns: dict = {}
        exec(_apply(source, rng=random.Random(0), params=_FAST), ns)
        assert ns["result"] == 7


class TestCrossReferences:
    """Verify that cross-scope junk references work correctly."""

    def test_cross_ref_code_executes_without_error(self) -> None:
        # With cross_ref_probability=1.0 all junk vars reference earlier ones.
        # The first injected var has no pool to draw from so is a literal;
        # subsequent ones reference earlier junk.
        params = InjectionParams(
            stmts_per_scope_min=5,
            stmts_per_scope_max=5,
            cross_ref_probability=1.0,
        )
        source = "x = 1\n"
        ns: dict = {}
        exec(_apply(source, rng=random.Random(0), params=params), ns)

    def test_zero_cross_ref_produces_only_literals(self) -> None:
        params = InjectionParams(
            stmts_per_scope_min=3,
            stmts_per_scope_max=3,
            cross_ref_probability=0.0,
        )
        result = _apply("x = 1", rng=random.Random(0), params=params)
        tree = ast.parse(result)
        # All junk assignment values should be constants (no Name references)
        junk_values = [
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id != "x"
        ]
        for val in junk_values:
            assert isinstance(
                val, ast.Constant
            ), f"Expected Constant, got {ast.dump(val)}"

    def test_inner_scope_intra_cross_ref_executes_without_error(self) -> None:
        # Cross-refs within a function body's own local junk must work.
        params = InjectionParams(
            stmts_per_scope_min=5,
            stmts_per_scope_max=5,
            cross_ref_probability=1.0,
        )
        source = textwrap.dedent(
            """\
            def foo():
                return 42
            result = foo()
            """
        )
        ns: dict = {}
        exec(_apply(source, rng=random.Random(5), params=params), ns)
        assert ns["result"] == 42
