from __future__ import annotations

import ast
import random
from dataclasses import dataclass
from typing import ClassVar

from ...helpers import RandomDataTypeGenerator, VariableNameGenerator
from ..base import ASTTransform, TechniqueMetadata
from ..registry import register
from .variable_renamer import _NameCollector

_MAX_NAME_ATTEMPTS = 200


def _interleave(
    original: list[ast.stmt],
    injected: list[ast.stmt],
    rng: random.Random,
) -> list[ast.stmt]:
    """Return a copy of *original* with *injected* statements scattered throughout.

    Each injected statement is assigned a random slot (gap between real
    statements) independently.  Critically, the *relative order* of injected
    statements is preserved: if injected[i] references a variable defined by
    injected[j] where j < i, injected[j] will always appear first, preventing
    NameErrors when cross-scope references are used.
    """
    if not injected:
        return list(original)
    n = len(original)
    # Sort slots to preserve relative order among injected stmts.
    slots = sorted(rng.randint(0, n) for _ in injected)

    junk_by_slot: list[list[ast.stmt]] = [[] for _ in range(n + 1)]
    for stmt, slot in zip(injected, slots):
        junk_by_slot[slot].append(stmt)

    result: list[ast.stmt] = []
    for i, real_stmt in enumerate(original):
        result.extend(junk_by_slot[i])
        result.append(real_stmt)
    result.extend(junk_by_slot[n])
    return result


@dataclass(frozen=True)
class InjectionParams:
    """Controls dead code injection density and cross-reference behaviour.

    ``stmts_per_scope_min`` / ``stmts_per_scope_max``
        Range of junk statements injected into each discovered scope
        (module body, function body, if-branch, for-body, …).

    ``cross_ref_probability``
        Probability [0, 1] that a new junk assignment reads from an already-
        created junk variable (from the same scope *or* an outer scope) rather
        than a fresh literal.  This creates convincing inter-variable "flow"
        that is still entirely dead.
    """

    stmts_per_scope_min: int = 3
    stmts_per_scope_max: int = 10
    cross_ref_probability: float = 0.35


@register
class DeadCodeInjector(ASTTransform):
    """Recursively injects dead variable assignments at every scope level.

    Unlike a flat module-level approach this transform walks the entire AST
    and injects into every statement list it finds — function bodies, class
    bodies, if/elif/else branches, for/while bodies, with-blocks, and
    try/except/finally handlers.

    Outer-scope junk names are passed *into* nested scopes so that inner dead
    code can reference them (read-only), creating the illusion that values flow
    through the program.  Junk names themselves are globally unique across all
    scopes to avoid any accidental shadowing.

    Pass a seeded :class:`random.Random` and/or custom :class:`InjectionParams`
    for reproducible output or tuned density::

        injector = DeadCodeInjector(
            rng=random.Random(42),
            params=InjectionParams(stmts_per_scope_min=1, stmts_per_scope_max=4),
        )
    """

    metadata: ClassVar[TechniqueMetadata] = TechniqueMetadata(
        name="dead_code_injector",
        description="Recursively injects dead code at every scope level.",
        priority=30,
    )

    def __init__(
        self,
        rng: random.Random | None = None,
        params: InjectionParams | None = None,
    ) -> None:
        self._rng = rng or random.Random()
        self._params = params or InjectionParams()

    # ------------------------------------------------------------------
    # ASTTransform entry point
    # ------------------------------------------------------------------

    def apply(self, tree: ast.Module) -> ast.Module:
        collector = _NameCollector()
        collector.visit(tree)

        # Initialise per-apply state (a new instance is created per pipeline
        # run, so this is safe to store on self).
        self._excluded: frozenset[str] = collector.all_bound_names
        self._seen: set[str] = set()
        self._counter: int = 0
        self._name_gen = VariableNameGenerator(rng=self._rng)
        self._data_gen = RandomDataTypeGenerator(rng=self._rng)

        self._inject_stmts(tree.body, outer_junk=frozenset())
        return super().apply(tree)

    # ------------------------------------------------------------------
    # Core injection helpers
    # ------------------------------------------------------------------

    def _fresh_name(self) -> str | None:
        """Return a name not already used anywhere in the module."""
        for _ in range(_MAX_NAME_ATTEMPTS):
            name = self._name_gen.get_random(self._counter + 1)
            self._counter += 1
            if name not in self._excluded and name not in self._seen:
                self._seen.add(name)
                return name
        return None  # safety guard — essentially unreachable in practice

    def _make_junk_stmt(
        self,
        local_junk: set[str],
    ) -> ast.stmt | None:
        """Build one dead assignment, optionally referencing existing local junk.

        Cross-references are intentionally limited to ``local_junk`` (names
        already injected in this same scope during the current call to
        ``_inject_stmts``).  Referencing ``outer_junk`` names would risk a
        ``NameError`` at runtime: module-level junk is randomly interleaved
        with real statements, so it may not yet be defined at the point where
        an inner scope (function, if-branch, …) reads it.  Since
        ``_interleave`` uses sorted slots, local junk stmts always appear in
        generation order, making intra-scope cross-references safe.
        """
        name = self._fresh_name()
        if name is None:
            return None

        available = list(local_junk)
        if available and self._rng.random() < self._params.cross_ref_probability:
            ref = self._rng.choice(available)
            value: ast.expr = ast.Name(id=ref, ctx=ast.Load())
        else:
            value = ast.Constant(value=self._data_gen.get_random())

        local_junk.add(name)
        return ast.Assign(
            targets=[ast.Name(id=name, ctx=ast.Store())],
            value=value,
        )

    def _inject_stmts(
        self,
        stmts: list[ast.stmt],
        outer_junk: frozenset[str],
    ) -> None:
        """Inject junk into *stmts* in-place, then recurse into nested scopes."""
        count = self._rng.randint(
            self._params.stmts_per_scope_min,
            self._params.stmts_per_scope_max,
        )
        local_junk: set[str] = set()
        new_stmts: list[ast.stmt] = []

        for _ in range(count * 10):
            if len(new_stmts) >= count:
                break
            stmt = self._make_junk_stmt(local_junk)
            if stmt is None:
                break
            new_stmts.append(stmt)

        stmts[:] = _interleave(stmts, new_stmts, self._rng)

        # Pass combined pool into nested scopes (read-only for outer names).
        combined = outer_junk | frozenset(local_junk)
        for stmt in stmts:
            self._recurse_into(stmt, combined)

    def _recurse_into(self, stmt: ast.stmt, outer_junk: frozenset[str]) -> None:
        """Dispatch injection into all statement lists nested inside *stmt*."""
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            self._inject_stmts(stmt.body, outer_junk)

        elif isinstance(stmt, ast.If):
            self._inject_stmts(stmt.body, outer_junk)
            if stmt.orelse:
                self._inject_stmts(stmt.orelse, outer_junk)

        elif isinstance(stmt, (ast.For, ast.While)):
            self._inject_stmts(stmt.body, outer_junk)
            if stmt.orelse:
                self._inject_stmts(stmt.orelse, outer_junk)

        elif isinstance(stmt, ast.With):
            self._inject_stmts(stmt.body, outer_junk)

        elif isinstance(stmt, ast.Try):
            self._inject_stmts(stmt.body, outer_junk)
            for handler in stmt.handlers:
                self._inject_stmts(handler.body, outer_junk)
            if stmt.orelse:
                self._inject_stmts(stmt.orelse, outer_junk)
            if stmt.finalbody:
                self._inject_stmts(stmt.finalbody, outer_junk)
