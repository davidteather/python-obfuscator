"""Obfuscation techniques package.

Importing this package triggers registration of all built-in techniques via
the ``@register`` decorator.  Third-party techniques can be registered by
importing their module before calling :func:`python_obfuscator.obfuscate`.
"""

# Side-effect import: populates the registry
from . import ast_transforms
from .base import ASTTransform, TechniqueMetadata
from .registry import all_technique_names, get_transforms, register

__all__ = [
    "ASTTransform",
    "TechniqueMetadata",
    "register",
    "all_technique_names",
    "get_transforms",
    "ast_transforms",
]
