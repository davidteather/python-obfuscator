"""End-to-end tests: run each file in tests/e2e/files/ before and after full
obfuscation and assert that stdout is identical.

A separate benchmark test measures the runtime overhead introduced by
obfuscation.  Benchmark tests always pass — they are informational and are
printed to the terminal when pytest is run with ``-s``.

Usage::

    pytest tests/e2e/ -v            # correctness only (fast)
    pytest tests/e2e/ -v -s         # correctness + benchmark output
    pytest tests/e2e/ -v -s -k benchmark  # benchmarks only
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from python_obfuscator import ObfuscationConfig, obfuscate

if TYPE_CHECKING:
    pass

# ── configuration ─────────────────────────────────────────────────────────────

E2E_DIR = Path(__file__).parent / "files"
E2E_FILES = sorted(E2E_DIR.glob("*.py"))

_BASELINE = ObfuscationConfig.only()  # no transforms — plain re-parse/unparse
_ALL = ObfuscationConfig.all_enabled()

#: Number of timed repetitions per file.  Enough for stable means without
#: making the suite slow under CI.
_BENCHMARK_RUNS = 20

# ── helpers ───────────────────────────────────────────────────────────────────


def _capture(code: str) -> list[str]:
    """Execute *code* and return every string passed to print(), in order.

    The fake ``print`` is injected into the exec namespace so it works even
    when ``exec_wrapper`` is active (the inner exec inherits the outer globals).
    """
    captured: list[str] = []

    def fake_print(*args: object, sep: str = " ", end: str = "\n", **_: object) -> None:
        captured.append(sep.join(str(a) for a in args))

    exec(code, {"print": fake_print})  # noqa: S102
    return captured


def _time_runs(code: str, n: int) -> float:
    """Execute *code* n times and return the total wall-clock seconds."""
    captured: list[str] = []

    def fake_print(*args: object, **_: object) -> None:
        captured.append(str(args))

    start = time.perf_counter()
    for _ in range(n):
        exec(code, {"print": fake_print})  # noqa: S102
    return time.perf_counter() - start


# ── correctness ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("py_file", E2E_FILES, ids=[f.stem for f in E2E_FILES])
def test_e2e_correctness(py_file: Path) -> None:
    """Obfuscated output must be byte-for-byte identical to the original."""
    source = py_file.read_text()
    expected = _capture(obfuscate(source, config=_BASELINE))
    actual = _capture(obfuscate(source, config=_ALL))
    assert actual == expected, (
        f"\nOutput mismatch for {py_file.name}:\n"
        f"  expected {len(expected)} line(s), got {len(actual)}\n"
        f"  first expected: {expected[:5]}\n"
        f"  first actual:   {actual[:5]}"
    )


# ── benchmark ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("py_file", E2E_FILES, ids=[f.stem for f in E2E_FILES])
def test_e2e_benchmark(py_file: Path) -> None:
    """Measure runtime overhead introduced by all obfuscation techniques.

    This test always passes.  Run with ``-s`` to see the timing table printed
    to stdout.
    """
    source = py_file.read_text()
    original_code = obfuscate(source, config=_BASELINE)
    obfuscated_code = obfuscate(source, config=_ALL)

    orig_t = _time_runs(original_code, _BENCHMARK_RUNS)
    obf_t = _time_runs(obfuscated_code, _BENCHMARK_RUNS)

    orig_ms = orig_t * 1000 / _BENCHMARK_RUNS
    obf_ms = obf_t * 1000 / _BENCHMARK_RUNS
    overhead_pct = (obf_ms / orig_ms - 1.0) * 100 if orig_ms > 0 else 0.0

    print(
        f"\n{'─' * 62}\n"
        f"  {py_file.name}\n"
        f"  original   : {orig_ms:8.3f} ms/run\n"
        f"  obfuscated : {obf_ms:8.3f} ms/run\n"
        f"  overhead   : {overhead_pct:+8.1f} %\n"
        f"  runs       : {_BENCHMARK_RUNS}\n"
    )


# ── per-technique breakdown ───────────────────────────────────────────────────


_TECHNIQUE_CONFIGS: list[tuple[str, ObfuscationConfig]] = [
    ("baseline (none)", ObfuscationConfig.only()),
    ("variable_renamer", ObfuscationConfig.only("variable_renamer")),
    ("string_hex_encoder", ObfuscationConfig.only("string_hex_encoder")),
    ("dead_code_injector", ObfuscationConfig.only("dead_code_injector")),
    ("exec_wrapper", ObfuscationConfig.only("exec_wrapper")),
    ("all techniques", ObfuscationConfig.all_enabled()),
]


@pytest.mark.parametrize("py_file", E2E_FILES, ids=[f.stem for f in E2E_FILES])
def test_e2e_per_technique_benchmark(py_file: Path) -> None:
    """Break down the runtime overhead contributed by each technique.

    Always passes; prints a table to stdout when run with ``-s``.
    """
    source = py_file.read_text()

    rows: list[tuple[str, float]] = []
    for label, cfg in _TECHNIQUE_CONFIGS:
        code = obfuscate(source, config=cfg)
        t = _time_runs(code, _BENCHMARK_RUNS)
        rows.append((label, t * 1000 / _BENCHMARK_RUNS))

    baseline_ms = rows[0][1]
    lines = [f"\n{'─' * 62}", f"  Per-technique breakdown: {py_file.name}"]
    for label, ms in rows:
        overhead = (ms / baseline_ms - 1.0) * 100 if baseline_ms > 0 else 0.0
        bar = "█" * max(0, int(overhead / 5))
        lines.append(f"  {label:22s} {ms:8.3f} ms  {overhead:+7.1f}%  {bar}")
    print("\n".join(lines))
