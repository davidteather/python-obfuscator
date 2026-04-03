from __future__ import annotations

import ast
from typing import ClassVar

from ..base import ASTTransform, TechniqueMetadata
from ..registry import register


@register
class ExecWrapper(ASTTransform):
    """Replaces the module body with a single ``exec('...')`` call.

    This reduces the program to one top-level statement.  Because the inner
    source is stored as an ``ast.Constant``, all quoting and escaping is
    handled by ``ast.unparse`` — no manual string escaping is needed.

    Priority 100 ensures this runs last so that all other AST transforms
    (variable renaming, string encoding, etc.) have already been applied to
    the inner code before it is embedded in the exec call.
    """

    metadata: ClassVar[TechniqueMetadata] = TechniqueMetadata(
        name="exec_wrapper",
        description="Replaces the module body with a single exec('...') call.",
        priority=100,
    )

    def apply(self, tree: ast.Module) -> ast.Module:
        inner_source = ast.unparse(tree)

        new_tree = ast.Module(
            body=[
                ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id="exec", ctx=ast.Load()),
                        args=[ast.Constant(value=inner_source)],
                        keywords=[],
                    )
                )
            ],
            type_ignores=[],
        )
        ast.fix_missing_locations(new_tree)
        return new_tree
