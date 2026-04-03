from __future__ import annotations

import ast
from abc import ABC
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class TechniqueMetadata:
    name: str
    description: str
    priority: int  # lower numbers run first


class ASTTransform(ast.NodeTransformer, ABC):
    """Base for all obfuscation transforms.

    Subclasses must define a class-level ``metadata`` attribute and implement
    one or more ``visit_*`` methods.  The entry point is :meth:`apply`, not
    :meth:`visit` directly — this ensures ``ast.fix_missing_locations`` is
    always called after the transform.
    """

    metadata: ClassVar[TechniqueMetadata]

    def apply(self, tree: ast.Module) -> ast.Module:
        result = self.visit(tree)
        if not isinstance(result, ast.Module):
            raise RuntimeError(
                f"{type(self).__name__}.visit() returned a non-Module node; "
                "transforms must not replace the top-level Module"
            )
        ast.fix_missing_locations(result)
        return result
