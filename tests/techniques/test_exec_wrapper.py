"""Tests for ExecWrapper."""

import ast
import textwrap

import python_obfuscator  # trigger registration
from python_obfuscator.techniques.ast_transforms.exec_wrapper import ExecWrapper
from python_obfuscator.techniques.registry import all_technique_names


def _apply(source: str) -> str:
    tree = ast.parse(source)
    return ast.unparse(ExecWrapper().apply(tree))


class TestExecWrapper:
    def test_is_registered(self) -> None:
        assert "exec_wrapper" in all_technique_names()

    def test_output_is_one_statement(self) -> None:
        tree = ast.parse(_apply("x = 1\ny = 2"))
        assert len(tree.body) == 1
        assert isinstance(tree.body[0], ast.Expr)

    def test_output_is_exec_call(self) -> None:
        tree = ast.parse(_apply("x = 1"))
        call = tree.body[0].value
        assert isinstance(call, ast.Call)
        assert isinstance(call.func, ast.Name)
        assert call.func.id == "exec"

    def test_simple_source_executes_correctly(self) -> None:
        source = "x = 10\ny = 20\nz = x + y\n"
        ns: dict = {}
        exec(_apply(source), ns)
        assert ns["z"] == 30

    def test_multiline_function_executes_correctly(self) -> None:
        source = textwrap.dedent(
            """\
            def add(a, b):
                return a + b
            result = add(3, 4)
            """
        )
        ns: dict = {}
        exec(_apply(source), ns)
        assert ns["result"] == 7

    def test_class_definition_executes_correctly(self) -> None:
        source = textwrap.dedent(
            """\
            class Counter:
                def __init__(self):
                    self.value = 0
                def increment(self):
                    self.value += 1
            c = Counter()
            c.increment()
            c.increment()
            """
        )
        ns: dict = {}
        exec(_apply(source), ns)
        assert ns["c"].value == 2

    def test_string_with_quotes_executes_correctly(self) -> None:
        source = "x = 'hello'\ny = \"world\"\n"
        ns: dict = {}
        exec(_apply(source), ns)
        assert ns["x"] == "hello"
        assert ns["y"] == "world"

    def test_string_with_backslash_executes_correctly(self) -> None:
        source = "import re\npattern = re.compile('\\\\d+')\n"
        ns: dict = {}
        exec(_apply(source), ns)

    def test_empty_source_executes_correctly(self) -> None:
        ns: dict = {}
        exec(_apply(""), ns)

    def test_apply_returns_module(self) -> None:
        tree = ast.parse("x = 1")
        result = ExecWrapper().apply(tree)
        assert isinstance(result, ast.Module)

    def test_apply_produces_compilable_tree(self) -> None:
        tree = ast.parse("x = 1\ny = 2")
        result = ExecWrapper().apply(tree)
        compile(result, "<string>", "exec")

    def test_inner_source_is_string_constant(self) -> None:
        tree = ast.parse("x = 42")
        result = ExecWrapper().apply(tree)
        call = result.body[0].value
        assert isinstance(call, ast.Call)
        inner = call.args[0]
        assert isinstance(inner, ast.Constant)
        assert isinstance(inner.value, str)
        assert "42" in inner.value
