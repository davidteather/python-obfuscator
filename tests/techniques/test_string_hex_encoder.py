"""Tests for StringHexEncoder."""

import ast
import textwrap

from python_obfuscator.techniques.ast_transforms.string_hex_encoder import (
    StringHexEncoder,
    _str_to_hex_call,
)


def _apply(source: str) -> str:
    tree = ast.parse(source)
    result = StringHexEncoder().apply(tree)
    return ast.unparse(result)


def _eval(source: str) -> object:
    """Execute source and return the value of the last expression."""
    ns: dict = {}
    exec(source, ns)
    return ns


class TestStrToHexCall:
    def test_produces_call_node(self) -> None:
        node = _str_to_hex_call("hello")
        assert isinstance(node, ast.Call)

    def test_result_evaluates_to_original_string(self) -> None:
        node = _str_to_hex_call("hello")
        source = ast.unparse(ast.fix_missing_locations(node))
        assert eval(source) == "hello"  # noqa: S307

    def test_empty_string(self) -> None:
        node = _str_to_hex_call("")
        source = ast.unparse(ast.fix_missing_locations(node))
        assert eval(source) == ""  # noqa: S307

    def test_unicode_string(self) -> None:
        node = _str_to_hex_call("café")
        source = ast.unparse(ast.fix_missing_locations(node))
        assert eval(source) == "café"  # noqa: S307

    def test_string_with_spaces(self) -> None:
        node = _str_to_hex_call("hello world")
        source = ast.unparse(ast.fix_missing_locations(node))
        assert eval(source) == "hello world"  # noqa: S307

    def test_string_with_quotes(self) -> None:
        node = _str_to_hex_call('say "hi"')
        source = ast.unparse(ast.fix_missing_locations(node))
        assert eval(source) == 'say "hi"'  # noqa: S307

    def test_hex_representation_is_visible_in_output(self) -> None:
        node = _str_to_hex_call("hi")
        source = ast.unparse(ast.fix_missing_locations(node))
        # 'hi' -> 68 69
        assert "6869" in source

    def test_uses_fromhex_decode_pattern(self) -> None:
        node = _str_to_hex_call("x")
        source = ast.unparse(ast.fix_missing_locations(node))
        assert "fromhex" in source
        assert "decode" in source


class TestStringHexEncoderTransform:
    def test_string_literal_is_replaced(self) -> None:
        result = _apply('x = "hello"')
        assert "hello" not in result
        assert "fromhex" in result

    def test_replacement_evaluates_to_original(self) -> None:
        source = 'x = "hello"'
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        assert ns["x"] == "hello"

    def test_integer_constant_is_unchanged(self) -> None:
        result = _apply("x = 42")
        assert "42" in result
        assert "fromhex" not in result

    def test_float_constant_is_unchanged(self) -> None:
        result = _apply("x = 3.14")
        assert "3.14" in result
        assert "fromhex" not in result

    def test_bytes_constant_is_unchanged(self) -> None:
        result = _apply("x = b'hello'")
        assert "fromhex" not in result

    def test_none_constant_is_unchanged(self) -> None:
        result = _apply("x = None")
        assert "fromhex" not in result

    def test_bool_constant_is_unchanged(self) -> None:
        result = _apply("x = True")
        assert "fromhex" not in result

    def test_empty_string_is_replaced(self) -> None:
        source = 'x = ""'
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        assert ns["x"] == ""

    def test_unicode_string_is_replaced(self) -> None:
        source = 'x = "café"'
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        assert ns["x"] == "café"

    def test_multiple_strings_in_file(self) -> None:
        source = textwrap.dedent(
            """\
            a = "foo"
            b = "bar"
            """
        )
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        assert ns["a"] == "foo"
        assert ns["b"] == "bar"

    def test_fstring_is_not_modified(self) -> None:
        source = 'name = "world"\ngreeting = f"hello {name}"'
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        assert ns["greeting"] == "hello world"

    def test_output_is_valid_python(self) -> None:
        source = textwrap.dedent(
            """\
            x = "test"
            y = 42
            z = "another"
            """
        )
        result = _apply(source)
        ast.parse(result)  # raises SyntaxError if invalid

    def test_nested_string_in_function(self) -> None:
        source = textwrap.dedent(
            """\
            def greet():
                return "hello"
            """
        )
        result = _apply(source)
        ns: dict = {}
        exec(result, ns)
        assert ns["greet"]() == "hello"

    def test_apply_calls_fix_missing_locations(self) -> None:
        """apply() must produce a tree that compiles without LocationError."""
        source = 'x = "hello"'
        tree = ast.parse(source)
        new_tree = StringHexEncoder().apply(tree)
        compile(new_tree, "<string>", "exec")  # should not raise
