import pytest

from python_obfuscator.techniques.base import ASTTransform, TechniqueMetadata
from python_obfuscator.techniques.registry import (
    _REGISTRY,
    all_technique_names,
    get_transforms,
    register,
)


class TestRegister:
    def test_known_transforms_are_registered(self) -> None:
        assert "variable_renamer" in _REGISTRY
        assert "string_hex_encoder" in _REGISTRY
        assert "dead_code_injector" in _REGISTRY
        assert "exec_wrapper" in _REGISTRY

    def test_register_invalid_type_raises_type_error(self) -> None:
        class NotATransform:
            metadata = TechniqueMetadata(name="bad", description="bad", priority=0)

        with pytest.raises(TypeError, match="must be a subclass"):
            register(NotATransform)  # type: ignore[arg-type]

    def test_register_returns_class_unchanged(self) -> None:
        class _Temp(ASTTransform):
            metadata = TechniqueMetadata(
                name="_temp_register_test", description="temp", priority=999
            )

        result = register(_Temp)
        assert result is _Temp
        _REGISTRY.pop("_temp_register_test", None)


class TestAllTechniqueNames:
    def test_returns_frozenset(self) -> None:
        assert isinstance(all_technique_names(), frozenset)

    def test_includes_all_known_techniques(self) -> None:
        names = all_technique_names()
        for expected in (
            "variable_renamer",
            "string_hex_encoder",
            "dead_code_injector",
            "exec_wrapper",
        ):
            assert expected in names

    def test_equals_registry_keys(self) -> None:
        assert all_technique_names() == frozenset(_REGISTRY)


class TestGetTransforms:
    def test_returns_only_enabled_techniques(self) -> None:
        transforms = get_transforms(frozenset({"variable_renamer"}))
        assert [cls.metadata.name for cls in transforms] == ["variable_renamer"]

    def test_empty_enabled_returns_empty(self) -> None:
        assert get_transforms(frozenset()) == []

    def test_unknown_name_is_silently_ignored(self) -> None:
        assert get_transforms(frozenset({"nonexistent"})) == []

    def test_sorted_by_priority_ascending(self) -> None:
        transforms = get_transforms(
            frozenset({"variable_renamer", "string_hex_encoder", "dead_code_injector"})
        )
        priorities = [cls.metadata.priority for cls in transforms]
        assert priorities == sorted(priorities)
