import ast
import textwrap

import pytest

import python_obfuscator
from python_obfuscator.config import ObfuscationConfig
from python_obfuscator.obfuscator import Obfuscator, _validate_config, obfuscate

SIMPLE_SOURCE = textwrap.dedent(
    """\
    x = 1
    y = 2
    result = x + y
    """
)


class TestValidateConfig:
    def test_valid_config_does_not_raise(self) -> None:
        _validate_config(ObfuscationConfig.all_enabled())

    def test_unknown_technique_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown technique"):
            _validate_config(ObfuscationConfig.only("does_not_exist"))

    def test_error_message_lists_available_techniques(self) -> None:
        with pytest.raises(ValueError, match="Available:"):
            _validate_config(ObfuscationConfig.only("bad_name"))


class TestObfuscateFunction:
    def test_returns_string(self) -> None:
        assert isinstance(obfuscate(SIMPLE_SOURCE), str)

    def test_none_config_uses_all_enabled(self) -> None:
        assert isinstance(obfuscate(SIMPLE_SOURCE, config=None), str)

    def test_explicit_config_is_respected(self) -> None:
        cfg = ObfuscationConfig.only("string_hex_encoder")
        result = obfuscate('x = "hello"', config=cfg)
        assert "fromhex" in result

    def test_empty_config_returns_unparsed_source(self) -> None:
        result = obfuscate("x = 1 + 2\n", config=ObfuscationConfig.only())
        assert "x = 1 + 2" in result

    def test_unknown_technique_raises(self) -> None:
        with pytest.raises(ValueError):
            obfuscate(SIMPLE_SOURCE, config=ObfuscationConfig.only("bad"))

    def test_output_is_valid_python(self) -> None:
        ast.parse(obfuscate(SIMPLE_SOURCE))


class TestObfuscatorClass:
    def test_instantiation_with_no_config(self) -> None:
        o = Obfuscator()
        assert o.config == ObfuscationConfig.all_enabled()

    def test_instantiation_with_explicit_config(self) -> None:
        cfg = ObfuscationConfig.only("variable_renamer")
        assert Obfuscator(cfg).config == cfg

    def test_instantiation_with_unknown_technique_raises(self) -> None:
        with pytest.raises(ValueError):
            Obfuscator(ObfuscationConfig.only("nonexistent"))

    def test_obfuscate_returns_string(self) -> None:
        assert isinstance(Obfuscator().obfuscate(SIMPLE_SOURCE), str)

    def test_obfuscate_output_is_valid_python(self) -> None:
        ast.parse(Obfuscator().obfuscate(SIMPLE_SOURCE))

    def test_obfuscate_called_multiple_times_is_safe(self) -> None:
        o = Obfuscator()
        assert isinstance(o.obfuscate("x = 1"), str)
        assert isinstance(o.obfuscate("y = 2"), str)
