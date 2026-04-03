from __future__ import annotations

from .base import ASTTransform

_REGISTRY: dict[str, type[ASTTransform]] = {}


def register(cls: type[ASTTransform]) -> type[ASTTransform]:
    """Class decorator that registers a transform with the global registry.

    Usage::

        @register
        class MyTransform(ASTTransform):
            metadata = TechniqueMetadata(name="my_transform", ...)
            ...
    """
    if not (isinstance(cls, type) and issubclass(cls, ASTTransform)):
        raise TypeError(f"{cls!r} must be a subclass of ASTTransform")
    _REGISTRY[cls.metadata.name] = cls
    return cls


def all_technique_names() -> frozenset[str]:
    """Return the names of every registered technique."""
    return frozenset(_REGISTRY)


def get_transforms(enabled: frozenset[str]) -> list[type[ASTTransform]]:
    """Return enabled transforms sorted by ascending priority."""
    transforms = [_REGISTRY[name] for name in enabled if name in _REGISTRY]
    return sorted(transforms, key=lambda cls: cls.metadata.priority)
