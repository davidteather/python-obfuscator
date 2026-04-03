"""Tests for the ASTTransform base class."""

import ast

import pytest

from python_obfuscator.techniques.base import ASTTransform, TechniqueMetadata


class _IdentityTransform(ASTTransform):
    """No-op transform that returns the tree unchanged."""

    metadata = TechniqueMetadata(name="_identity", description="identity", priority=0)


class _BadTransform(ASTTransform):
    """Deliberately returns the wrong node type from visit_Module."""

    metadata = TechniqueMetadata(name="_bad_transform", description="bad", priority=0)

    def visit_Module(self, node: ast.Module) -> ast.Name:  # type: ignore[override]
        return ast.Name(id="x", ctx=ast.Load())


class TestASTTransformApply:
    def test_apply_returns_module(self) -> None:
        tree = ast.parse("x = 1")
        result = _IdentityTransform().apply(tree)
        assert isinstance(result, ast.Module)

    def test_apply_calls_fix_missing_locations(self) -> None:
        tree = ast.parse("x = 1")
        result = _IdentityTransform().apply(tree)
        compile(result, "<string>", "exec")  # fails if locations missing

    def test_apply_raises_runtime_error_on_non_module_return(self) -> None:
        tree = ast.parse("x = 1")
        with pytest.raises(RuntimeError, match="returned a non-Module node"):
            _BadTransform().apply(tree)

    def test_apply_error_message_includes_class_name(self) -> None:
        tree = ast.parse("x = 1")
        with pytest.raises(RuntimeError, match="_BadTransform"):
            _BadTransform().apply(tree)


class TestTechniqueMetadata:
    def test_fields_are_accessible(self) -> None:
        m = TechniqueMetadata(name="foo", description="bar", priority=5)
        assert m.name == "foo"
        assert m.description == "bar"
        assert m.priority == 5

    def test_metadata_is_frozen(self) -> None:
        m = TechniqueMetadata(name="foo", description="bar", priority=5)
        with pytest.raises((AttributeError, TypeError)):
            m.name = "other"  # type: ignore[misc]
