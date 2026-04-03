# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).  
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — AST-Based Rewrite

Complete rewrite from a regex-based implementation to a fully AST-based pipeline.

### Added

- **`ObfuscationConfig`** — immutable frozen dataclass for selecting techniques.
  Factory methods: `all_enabled()`, `only(*names)`, `.without(*names)`, `.with_added(*names)`.
- **Technique registry** — `@register` class decorator; techniques self-register by name.
  `all_technique_names()` and `get_transforms(enabled)` for pipeline construction.
- **`variable_renamer`** — two-pass AST renamer.  First pass collects renameable names
  (excludes builtins, imports, dunders, and attribute-accessed names); second pass applies
  the mapping.  Also renames `nonlocal` and `global` statement name lists.
- **`string_hex_encoder`** — converts string literals to `bytes.fromhex(…).decode('utf-8')`
  call nodes.  Skips f-strings where replacing a `Constant` with a `Call` is invalid.
- **`dead_code_injector`** — recursively injects dead variable assignments at every scope
  level: module body, function bodies, class bodies, if/for/while/try/with branches.
  Some assignments reference earlier dead variables (intra-scope cross-references) to
  simulate computation.  Accepts `InjectionParams` and a seeded `random.Random` for
  reproducible output.
- **`exec_wrapper`** — wraps the entire module in `exec(ast.unparse(tree))`, reducing the
  top-level AST to one statement.
- **`Obfuscator` class** — caches the transform pipeline across multiple `obfuscate()` calls.
- **`obfuscate()` module-level helper** — convenience wrapper for one-shot use.
- **CLI** (`pyobfuscate`) — `--disable/-d` flag accepts technique names; `--stdout`; `--version/-V`.
- **E2E test suite** with correctness and benchmark tests across six complex programs.
- **Per-technique runtime benchmarks** showing individual overhead contribution.
- 100 % branch coverage enforced in CI.
- Python 3.10–3.14 test matrix.

### Changed

- Priority ordering now encoded in `TechniqueMetadata.priority` rather than list position.
- `VariableNameGenerator` and `RandomDataTypeGenerator` accept an optional `rng` argument
  for deterministic testing.
- `_NameCollector` exposes `all_bound_names` (assigned + imported + builtins) for use by
  the dead-code injector's exclusion set.

### Removed

- All regex-based technique implementations (`techniques.py`).
- `regex` runtime dependency (was used only for the old hex-encoding approach).
- `SourceTransform` base class and `source_transforms` package.

### Fixed

- `VariableRenamer` now updates `nonlocal` and `global` statement name lists, preventing
  `SyntaxError: no binding for nonlocal '…' found` after renaming.
- `VariableRenamer` excludes attribute-accessed names from renaming to prevent
  `AttributeError` when calling methods by the original name after their definition is renamed.
- `_interleave` preserves relative ordering of injected statements (sorted random slots)
  so intra-scope cross-references never appear before their definitions.

---

## [0.0.2] — prior release

Initial public release with regex-based obfuscation techniques.

- `one_liner` — collapsed newlines into semicolons (superceded by `exec_wrapper`).
- `variable_renamer` — regex-based name replacement.
- `add_random_variables` — prepended/appended random assignments at module level.
- `str_to_hex_bytes` — regex-based string-to-hex conversion.
