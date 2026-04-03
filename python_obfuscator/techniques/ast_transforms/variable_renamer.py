from __future__ import annotations

import ast
import builtins
import re
from typing import ClassVar

from ...helpers import VariableNameGenerator
from ..base import ASTTransform, TechniqueMetadata
from ..registry import register

_BUILTIN_NAMES: frozenset[str] = frozenset(dir(builtins))
_DUNDER_RE: re.Pattern[str] = re.compile(r"^__\w+__$")


class _NameCollector(ast.NodeVisitor):
    """First-pass visitor that identifies every name eligible for renaming.

    A name is *ineligible* if it is:
    - a Python builtin (``print``, ``len``, etc.)
    - bound by an import statement
    - a dunder (``__name__``, ``__doc__``, etc.)

    Limitation: scope is not tracked. The same identifier appearing in
    different scopes will map to the same obfuscated name.  This is
    semantically correct for non-shadowing code but may produce surprising
    results when the same name is reused in sibling scopes.
    """

    def __init__(self) -> None:
        self._imported: set[str] = set()
        self._assigned: set[str] = set()
        self._attr_accessed: set[str] = set()

    @property
    def renameable(self) -> frozenset[str]:
        return frozenset(
            name
            for name in self._assigned
            if name not in _BUILTIN_NAMES
            and name not in self._imported
            and not _DUNDER_RE.match(name)
            and name not in self._attr_accessed
        )

    @property
    def all_bound_names(self) -> frozenset[str]:
        """Every name that is assigned or imported, plus all builtins.

        Use this as the exclusion set when generating junk names so that
        injected variables never shadow real ones.
        """
        return frozenset(self._assigned) | frozenset(self._imported) | _BUILTIN_NAMES

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound = alias.asname or alias.name.split(".")[0]
            self._imported.add(bound)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                continue  # can't know statically what names are introduced
            bound = alias.asname or alias.name
            self._imported.add(bound)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self._assigned.add(node.id)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._assigned.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._assigned.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._assigned.add(node.name)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Attribute names (obj.name) are stored as bare strings in the AST.
        # We cannot update call sites without full type analysis, so any name
        # that appears as an attribute accessor is excluded from renaming.
        self._attr_accessed.add(node.attr)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        self._assigned.add(node.arg)
        # Do not recurse: we intentionally skip renaming annotation names


@register
class VariableRenamer(ASTTransform):
    """Renames variables, functions, classes, and parameters to unreadable names.

    Uses a two-pass approach:
    1. :class:`_NameCollector` walks the tree to build the rename mapping.
    2. The :class:`ast.NodeTransformer` machinery applies the mapping.
    """

    metadata: ClassVar[TechniqueMetadata] = TechniqueMetadata(
        name="variable_renamer",
        description="Renames local variables, functions, and parameters to hard-to-read identifiers.",
        priority=10,
    )

    def __init__(self) -> None:
        self._rename_map: dict[str, str] = {}

    def apply(self, tree: ast.Module) -> ast.Module:
        collector = _NameCollector()
        collector.visit(tree)

        name_gen = VariableNameGenerator()
        # Sort for deterministic ordering given the same input
        self._rename_map = {
            name: name_gen.get_random(i + 1)
            for i, name in enumerate(sorted(collector.renameable))
        }

        return super().apply(tree)

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self._rename_map:
            node.id = self._rename_map[node.id]
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.name in self._rename_map:
            node.name = self._rename_map[node.name]
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        if node.name in self._rename_map:
            node.name = self._rename_map[node.name]
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        if node.name in self._rename_map:
            node.name = self._rename_map[node.name]
        self.generic_visit(node)
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        if node.arg in self._rename_map:
            node.arg = self._rename_map[node.arg]
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Nonlocal:
        node.names = [self._rename_map.get(n, n) for n in node.names]
        return node

    def visit_Global(self, node: ast.Global) -> ast.Global:
        node.names = [self._rename_map.get(n, n) for n in node.names]
        return node
