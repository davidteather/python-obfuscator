"""Tests for VariableRenamer."""

import ast
import textwrap

from python_obfuscator.techniques.ast_transforms.variable_renamer import (
    VariableRenamer,
    _NameCollector,
)


def _apply(source: str) -> str:
    tree = ast.parse(source)
    result = VariableRenamer().apply(tree)
    return ast.unparse(result)


def _collect(source: str) -> frozenset[str]:
    tree = ast.parse(source)
    collector = _NameCollector()
    collector.visit(tree)
    return collector.renameable


class TestNameCollector:
    def test_collects_simple_assignment(self) -> None:
        assert "x" in _collect("x = 1")

    def test_does_not_collect_builtin_names(self) -> None:
        renameable = _collect("print('hello')\nx = len([1, 2])")
        assert "print" not in renameable
        assert "len" not in renameable

    def test_does_not_collect_imported_name(self) -> None:
        renameable = _collect("import os\npath = os.getcwd()")
        assert "os" not in renameable

    def test_does_not_collect_from_import_name(self) -> None:
        renameable = _collect("from pathlib import Path\np = Path('.')")
        assert "Path" not in renameable

    def test_collects_alias_of_import(self) -> None:
        renameable = _collect("import os as operating_system\nx = 1")
        assert "operating_system" not in renameable
        assert "x" in renameable

    def test_from_import_with_asname_excluded(self) -> None:
        renameable = _collect("from os import path as p\nx = 1")
        assert "p" not in renameable

    def test_star_import_does_not_crash(self) -> None:
        renameable = _collect("from os.path import *\nx = 1")
        assert "x" in renameable

    def test_does_not_collect_dunder_names(self) -> None:
        renameable = _collect("__name__ = 'main'\nx = 1")
        assert "__name__" not in renameable
        assert "x" in renameable

    def test_collects_function_name(self) -> None:
        assert "my_func" in _collect("def my_func(): pass")

    def test_collects_async_function_name(self) -> None:
        assert "my_coro" in _collect("async def my_coro(): pass")

    def test_collects_class_name(self) -> None:
        assert "MyClass" in _collect("class MyClass: pass")

    def test_collects_function_argument(self) -> None:
        renameable = _collect("def foo(bar): pass")
        assert "bar" in renameable

    def test_collects_for_loop_variable(self) -> None:
        assert "item" in _collect("for item in range(10): pass")

    def test_does_not_collect_load_context_name(self) -> None:
        # 'y' is only loaded, never stored
        renameable = _collect("x = y + 1")
        assert "y" not in renameable

    def test_does_not_collect_builtin_even_if_shadowed(self) -> None:
        renameable = _collect("list = [1, 2, 3]")
        assert "list" not in renameable


class TestVariableRenamer:
    def test_renames_simple_variable(self) -> None:
        result = _apply("my_variable = 42")
        assert "my_variable" not in result

    def test_renamed_code_produces_same_value(self) -> None:
        source = textwrap.dedent(
            """\
            x = 10
            y = 20
            z = x + y
            """
        )
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        values = {v for k, v in ns.items() if not k.startswith("__")}
        assert 30 in values

    def test_builtin_names_not_renamed(self) -> None:
        source = "result = len([1, 2, 3])"
        result = _apply(source)
        assert "len" in result

    def test_import_name_not_renamed(self) -> None:
        source = "import os\npath = os.getcwd()"
        result = _apply(source)
        assert "os" in result

    def test_dunder_not_renamed(self) -> None:
        source = "if __name__ == '__main__': pass"
        result = _apply(source)
        assert "__name__" in result

    def test_function_name_is_renamed(self) -> None:
        source = "def compute(): return 42"
        result = _apply(source)
        assert "compute" not in result

    def test_renamed_function_still_callable(self) -> None:
        source = textwrap.dedent(
            """\
            def add(a, b):
                return a + b
            """
        )
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        funcs = [v for v in ns.values() if callable(v)]
        assert len(funcs) == 1
        assert funcs[0](3, 4) == 7

    def test_function_argument_is_renamed(self) -> None:
        source = "def foo(my_arg): return my_arg"
        result = _apply(source)
        assert "my_arg" not in result

    def test_renamed_argument_still_works(self) -> None:
        source = "def identity(value): return value"
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        funcs = [v for v in ns.values() if callable(v)]
        assert funcs[0](99) == 99

    def test_class_name_is_renamed(self) -> None:
        source = "class MyClass: pass"
        result = _apply(source)
        assert "MyClass" not in result

    def test_async_function_name_is_renamed(self) -> None:
        source = "async def my_coro(): pass"
        result = _apply(source)
        assert "my_coro" not in result

    def test_same_name_renamed_consistently(self) -> None:
        source = textwrap.dedent(
            """\
            counter = 0
            counter = counter + 1
            result = counter
            """
        )
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        values = {v for k, v in ns.items() if not k.startswith("__")}
        assert 1 in values

    def test_output_is_valid_python(self) -> None:
        source = textwrap.dedent(
            """\
            def process(items):
                total = 0
                for item in items:
                    total += item
                return total
            """
        )
        result = _apply(source)
        ast.parse(result)

    def test_for_loop_variable_renamed(self) -> None:
        source = textwrap.dedent(
            """\
            total = 0
            for num in range(5):
                total += num
            """
        )
        result = _apply(source)
        assert "num" not in result
        ns: dict = {}
        exec(result, ns)
        values = {v for k, v in ns.items() if not k.startswith("__")}
        assert 10 in values

    def test_apply_produces_compilable_tree(self) -> None:
        source = "x = 1\ndef foo(a): return a"
        tree = ast.parse(source)
        new_tree = VariableRenamer().apply(tree)
        compile(new_tree, "<string>", "exec")

    def test_multiple_calls_independent(self) -> None:
        """Two separate VariableRenamer instances do not share state."""
        source = "value = 5"
        r1 = _apply(source)
        r2 = _apply(source)
        # Both are valid Python; they may or may not produce the same name
        # (random), but neither should contain the original name.
        assert "value" not in r1
        assert "value" not in r2


class TestVariableRenamerFalseBranches:
    """Cover the 'name NOT in rename_map' branches in each visit_* method."""

    def _make_renamer_with_empty_map(self) -> VariableRenamer:
        renamer = VariableRenamer()
        renamer._rename_map = {}
        return renamer

    def test_visit_name_unchanged_when_not_in_map(self) -> None:
        renamer = self._make_renamer_with_empty_map()
        node = ast.Name(id="foo", ctx=ast.Load())
        result = renamer.visit_Name(node)
        assert result.id == "foo"

    def test_visit_function_def_unchanged_when_not_in_map(self) -> None:
        renamer = self._make_renamer_with_empty_map()
        func_node = ast.parse("def my_func(): pass").body[0]
        assert isinstance(func_node, ast.FunctionDef)
        result = renamer.visit_FunctionDef(func_node)
        assert result.name == "my_func"

    def test_visit_async_function_def_unchanged_when_not_in_map(self) -> None:
        renamer = self._make_renamer_with_empty_map()
        func_node = ast.parse("async def my_coro(): pass").body[0]
        assert isinstance(func_node, ast.AsyncFunctionDef)
        result = renamer.visit_AsyncFunctionDef(func_node)
        assert result.name == "my_coro"

    def test_visit_class_def_unchanged_when_not_in_map(self) -> None:
        renamer = self._make_renamer_with_empty_map()
        class_node = ast.parse("class MyClass: pass").body[0]
        assert isinstance(class_node, ast.ClassDef)
        result = renamer.visit_ClassDef(class_node)
        assert result.name == "MyClass"

    def test_visit_arg_unchanged_when_not_in_map(self) -> None:
        renamer = self._make_renamer_with_empty_map()
        arg_node = ast.arg(arg="my_param")
        result = renamer.visit_arg(arg_node)
        assert result.arg == "my_param"

    def test_builtin_named_function_not_renamed_during_apply(self) -> None:
        # 'list' is a builtin; when a function is defined with that name it
        # must be excluded from the rename map so visit_FunctionDef takes the
        # false branch in a real apply() call.
        source = "def list(x): return x"
        result = _apply(source)
        assert "list" in result

    def test_visit_nonlocal_renames_known_names(self) -> None:
        # If nonlocal is not updated when 'count' is renamed, Python raises
        # SyntaxError: no binding for nonlocal 'count' found.
        source = textwrap.dedent(
            """\
            def outer():
                count = 0
                def inner():
                    nonlocal count
                    count += 1
                    return count
                return inner
            result = outer()()
            """
        )
        ns: dict = {}
        exec(_apply(source), ns)
        # 'result' is renamed; locate the int value in the namespace.
        result_val = next(
            v for k, v in ns.items() if k != "__builtins__" and isinstance(v, int)
        )
        assert result_val == 1

    def test_visit_global_renames_known_names(self) -> None:
        # If global is not updated when 'counter' is renamed, the renamed
        # increment() will refer to a non-existent global name.
        source = textwrap.dedent(
            """\
            counter = 0
            def increment():
                global counter
                counter += 1
            increment()
            result = counter
            """
        )
        ns: dict = {}
        exec(_apply(source), ns)
        result_val = next(
            v for k, v in ns.items() if k != "__builtins__" and isinstance(v, int)
        )
        assert result_val == 1
