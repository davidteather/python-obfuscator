from __future__ import annotations

import ast

from .config import ObfuscationConfig
from .techniques.registry import all_technique_names, get_transforms


def _validate_config(config: ObfuscationConfig) -> None:
    unknown = config.enabled_techniques - all_technique_names()
    if unknown:
        raise ValueError(
            f"Unknown technique(s): {sorted(unknown)}. "
            f"Available: {sorted(all_technique_names())}"
        )


def obfuscate(source: str, config: ObfuscationConfig | None = None) -> str:
    """Obfuscate *source* using the techniques described by *config*.

    When *config* is ``None`` all registered techniques are applied.
    """
    resolved = config if config is not None else ObfuscationConfig.all_enabled()
    _validate_config(resolved)

    tree = ast.parse(source)
    for transform_cls in get_transforms(resolved.enabled_techniques):
        tree = transform_cls().apply(tree)
    return ast.unparse(tree)


class Obfuscator:
    """Stateful wrapper that pre-builds and caches the transform pipeline.

    Prefer this over the module-level :func:`obfuscate` when processing many
    files with the same configuration, since the pipeline is validated and
    sorted once at construction time.
    """

    def __init__(self, config: ObfuscationConfig | None = None) -> None:
        self._config = config if config is not None else ObfuscationConfig.all_enabled()
        _validate_config(self._config)
        self._transforms = get_transforms(self._config.enabled_techniques)

    @property
    def config(self) -> ObfuscationConfig:
        return self._config

    def obfuscate(self, source: str) -> str:
        tree = ast.parse(source)
        for transform_cls in self._transforms:
            tree = transform_cls().apply(tree)
        return ast.unparse(tree)
