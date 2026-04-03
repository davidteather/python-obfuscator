# python-obfuscator

[![CI](https://github.com/davidteather/python-obfuscator/actions/workflows/package-test.yml/badge.svg)](https://github.com/davidteather/python-obfuscator/actions/workflows/package-test.yml)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/davidteather/python-obfuscator?style=flat-square)](https://github.com/davidteather/python-obfuscator/releases)
[![Downloads](https://static.pepy.tech/personalized-badge/python-obfuscator?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Downloads)](https://pypi.org/project/python-obfuscator/)
[![Codecov](https://codecov.io/gh/davidteather/python-obfuscator/branch/main/graph/badge.svg)](https://codecov.io/gh/davidteather/python-obfuscator)

A Python source-code obfuscator built on the standard-library `ast` module.  It applies multiple independent techniques — each individually togglable — to make code harder to read while keeping it fully executable.  See [Known limitations](#known-limitations) before use.

If this project is useful to you, consider [sponsoring development](https://github.com/sponsors/davidteather).

---

## Installing

```bash
pip install python-obfuscator
```

Requires Python ≥ 3.10.

### From source (contributors)

```bash
pip install -e ".[dev]"
```

Or with [Poetry](https://python-poetry.org/):

```bash
poetry install
```

(`poetry install` pulls dev dependencies from the lockfile; use `poetry run <command>` to run tools inside that environment.)

---

## Quick start — CLI

```bash
# Writes obfuscated/your_file.py (path structure is preserved)
pyobfuscate -i your_file.py

# Print to stdout
pyobfuscate -i your_file.py --stdout

# Disable specific techniques
pyobfuscate -i your_file.py --disable dead_code_injector --disable exec_wrapper

# Show version
pyobfuscate --version
```

---

## Python API

### One-shot helper

```python
from python_obfuscator import obfuscate

source = "x = 1\nprint(x + 2)"
result = obfuscate(source)
print(result)
```

### Selective techniques

```python
from python_obfuscator import obfuscate, ObfuscationConfig

# All techniques except dead-code injection
config = ObfuscationConfig.all_enabled().without("dead_code_injector")
result = obfuscate(source, config=config)

# Only string encoding
config = ObfuscationConfig.only("string_hex_encoder")
result = obfuscate(source, config=config)
```

### Reusing across multiple files (caches the pipeline)

```python
from python_obfuscator import Obfuscator, ObfuscationConfig

obf = Obfuscator(ObfuscationConfig.all_enabled())
for path in my_files:
    path.write_text(obf.obfuscate(path.read_text()))
```

### Config combinators

```python
cfg = ObfuscationConfig.all_enabled()   # every registered technique
cfg = ObfuscationConfig.only("variable_renamer", "exec_wrapper")
cfg = cfg.without("exec_wrapper")       # returns a new frozen config
cfg = cfg.with_added("dead_code_injector")
```

---

## Techniques

| Name | Priority | What it does |
|------|----------|--------------|
| `variable_renamer` | 10 | Renames local variables, function names, parameters, and class names to visually ambiguous identifiers (`lIIllIlI…`). Excludes builtins, imports, dunders, and attribute-accessed names. |
| `string_hex_encoder` | 20 | Replaces every string literal `"hi"` with `bytes.fromhex('6869').decode('utf-8')`. Skips f-strings. |
| `dead_code_injector` | 30 | Injects dead variable assignments at **every scope level** — module body, function bodies, class bodies, if/for/while/try/with branches. Some assignments reference other dead variables to simulate computation. |
| `exec_wrapper` | 100 | Wraps the entire module in a single `exec("…")` call, reducing the top-level AST to one statement. Runs last. |

Techniques are applied in priority order (lowest first).

---

## Example

**Input**

```python
def greet(name):
    msg = "Hello, " + name
    print(msg)

greet("world")
```

**Output** (all techniques enabled — abridged)

```python
exec('def lIlIllI(IIlIlII):\n    lIllIlI = bytes.fromhex(\'48656c6c6f2c20\').decode(\'utf-8\') + IIlIlII\n    ...\nlIlIllI(bytes.fromhex(\'776f726c64\').decode(\'utf-8\'))')
```

---

## Performance overhead

Benchmarks run on an Apple M-series machine, 20 iterations each.  The test programs cover OOP, algorithms, functional patterns, number theory, and string processing.

### Total overhead (all techniques)

| Program | Original | Obfuscated | Overhead |
|---------|----------|------------|---------|
| `algorithms.py` | 0.94 ms | 1.98 ms | +112% |
| `cipher.py` | 1.37 ms | 2.67 ms | +95% |
| `data_structures.py` | 0.72 ms | 2.20 ms | +207% |
| `functional.py` | 0.67 ms | 1.71 ms | +155% |
| `number_theory.py` | 1.84 ms | 3.16 ms | +72% |
| `oop_simulation.py` | 0.68 ms | 1.66 ms | +144% |

### Per-technique contribution (average across all programs)

| Technique | Avg overhead | Notes |
|-----------|-------------|-------|
| `variable_renamer` | ~5% | Pure rename — negligible at runtime |
| `string_hex_encoder` | ~12% | `bytes.fromhex` call per string literal |
| `dead_code_injector` | ~85% | Dominant cost — dead assignments execute every iteration |
| `exec_wrapper` | ~2% | Single extra `exec` layer |

The dead-code injector's overhead scales with the number of scopes and loop iterations in the original program.  Programs with tight inner loops see the most overhead.

---

## Known limitations

- **Class method names are not renamed.** Attribute-accessed names (`obj.method`) cannot be safely renamed without full type-inference, so the renamer conservatively excludes them.
- **Keyword argument names are not renamed.** `fn(key=val)` call-site keyword strings are bare AST strings, not `Name` nodes, and are not updated when a parameter is renamed.
- **No scope-aware renaming.** The same identifier used in two independent function scopes maps to the same obfuscated name (which is semantically correct but less obfuscated than it could be).
- **No control-flow obfuscation.** Opaque predicates, bogus branches, and integer encoding are not implemented.

---

## Running the test suite

After a dev install ([from source](#from-source-contributors)):

```bash
pytest
```

Coverage is enforced at ≥ 95% on every CI run.

```bash
# With coverage report
coverage run -m pytest && coverage report

# E2E tests with benchmark output
pytest tests/e2e/ -v -s
```

With Poetry, run the same commands through the project environment, for example `poetry run pytest`, `poetry run coverage run -m pytest`, and `poetry run pytest tests/e2e/ -v -s`.

---

## Authors

**David Teather** — [davidteather](https://github.com/davidteather)

## License

MIT — see [LICENSE](LICENSE).
