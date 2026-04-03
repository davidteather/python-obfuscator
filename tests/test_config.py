import pytest

from python_obfuscator.config import ObfuscationConfig
from python_obfuscator.techniques.registry import all_technique_names


class TestObfuscationConfig:
    def test_all_enabled_contains_all_registered(self) -> None:
        cfg = ObfuscationConfig.all_enabled()
        assert cfg.enabled_techniques == all_technique_names()

    def test_all_enabled_is_non_empty(self) -> None:
        cfg = ObfuscationConfig.all_enabled()
        assert len(cfg.enabled_techniques) > 0

    def test_only_restricts_to_given_names(self) -> None:
        cfg = ObfuscationConfig.only("variable_renamer")
        assert cfg.enabled_techniques == frozenset({"variable_renamer"})

    def test_only_multiple_names(self) -> None:
        cfg = ObfuscationConfig.only("variable_renamer", "string_hex_encoder")
        assert cfg.enabled_techniques == frozenset(
            {"variable_renamer", "string_hex_encoder"}
        )

    def test_only_zero_names_produces_empty(self) -> None:
        cfg = ObfuscationConfig.only()
        assert cfg.enabled_techniques == frozenset()

    def test_without_removes_named_technique(self) -> None:
        cfg = ObfuscationConfig.all_enabled().without("variable_renamer")
        assert "variable_renamer" not in cfg.enabled_techniques

    def test_without_keeps_other_techniques(self) -> None:
        cfg = ObfuscationConfig.all_enabled().without("variable_renamer")
        assert "string_hex_encoder" in cfg.enabled_techniques

    def test_without_unknown_name_is_a_noop(self) -> None:
        cfg = ObfuscationConfig.all_enabled()
        cfg2 = cfg.without("nonexistent_technique")
        assert cfg2.enabled_techniques == cfg.enabled_techniques

    def test_without_multiple_names(self) -> None:
        cfg = ObfuscationConfig.all_enabled().without(
            "variable_renamer", "string_hex_encoder"
        )
        assert "variable_renamer" not in cfg.enabled_techniques
        assert "string_hex_encoder" not in cfg.enabled_techniques

    def test_with_added_adds_names(self) -> None:
        cfg = ObfuscationConfig.only("variable_renamer").with_added(
            "string_hex_encoder"
        )
        assert "variable_renamer" in cfg.enabled_techniques
        assert "string_hex_encoder" in cfg.enabled_techniques

    def test_with_added_duplicate_is_idempotent(self) -> None:
        cfg = ObfuscationConfig.only("variable_renamer").with_added("variable_renamer")
        assert cfg.enabled_techniques == frozenset({"variable_renamer"})

    def test_config_is_immutable(self) -> None:
        cfg = ObfuscationConfig.all_enabled()
        with pytest.raises((AttributeError, TypeError)):
            cfg.enabled_techniques = frozenset()  # type: ignore[misc]

    def test_configs_are_equal_with_same_techniques(self) -> None:
        a = ObfuscationConfig.only("variable_renamer")
        b = ObfuscationConfig.only("variable_renamer")
        assert a == b

    def test_configs_differ_with_different_techniques(self) -> None:
        a = ObfuscationConfig.only("variable_renamer")
        b = ObfuscationConfig.only("string_hex_encoder")
        assert a != b
