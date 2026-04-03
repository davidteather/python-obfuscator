"""Smoke test: obfuscated output must execute and preserve semantics."""

import textwrap

import python_obfuscator
from python_obfuscator import ObfuscationConfig, Obfuscator, obfuscate


def test_default_obfuscation_preserves_computation() -> None:
    source = textwrap.dedent(
        """\
        v1 = 0
        v2 = 0
        v4 = 10
        assert v4 + v4 == 20
        assert v1 + v2 == 0
        """
    )
    result = obfuscate(source)
    exec(result)  # must not raise


def test_obfuscator_class_smoke() -> None:
    o = Obfuscator()
    result = o.obfuscate("x = 1 + 2")
    assert isinstance(result, str)


def test_obfuscator_with_subset_config() -> None:
    cfg = ObfuscationConfig.only("string_hex_encoder")
    result = obfuscate('greeting = "hello"', config=cfg)
    assert "fromhex" in result
    ns: dict = {}
    exec(result, ns)
    assert ns["greeting"] == "hello"
