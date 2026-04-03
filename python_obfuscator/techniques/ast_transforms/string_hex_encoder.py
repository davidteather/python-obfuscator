from __future__ import annotations

import ast
from typing import ClassVar

from ..base import ASTTransform, TechniqueMetadata
from ..registry import register


def _str_to_hex_call(value: str) -> ast.Call:
    """Build a ``bytes.fromhex('...').decode('utf-8')`` AST node.

    This is the canonical replacement for a string literal: it produces
    valid Python that evaluates to the original string while making the
    content unreadable without execution.
    """
    hex_value = value.encode("utf-8").hex()
    return ast.Call(
        func=ast.Attribute(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="bytes", ctx=ast.Load()),
                    attr="fromhex",
                    ctx=ast.Load(),
                ),
                args=[ast.Constant(value=hex_value)],
                keywords=[],
            ),
            attr="decode",
            ctx=ast.Load(),
        ),
        args=[ast.Constant(value="utf-8")],
        keywords=[],
    )


@register
class StringHexEncoder(ASTTransform):
    """Replaces string literals with ``bytes.fromhex(...).decode('utf-8')``."""

    metadata: ClassVar[TechniqueMetadata] = TechniqueMetadata(
        name="string_hex_encoder",
        description=(
            "Encodes string literals to bytes.fromhex(...).decode('utf-8') "
            "calls, hiding their content."
        ),
        priority=20,
    )

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if not isinstance(node.value, str):
            return node
        return ast.copy_location(_str_to_hex_call(node.value), node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:
        # f-strings embed Constant nodes for their literal parts, but the
        # semantics differ from top-level string constants.  Replacing them
        # with Call nodes would produce invalid AST inside a JoinedStr, so we
        # skip f-strings entirely.
        # TODO: we could split this out to a new technique in the future.
        # consider also over-doing f strings wiht some random strings/args places around
        return node
