from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObfuscationConfig:
    """Immutable configuration describing which techniques are enabled.

    Prefer the factory classmethods over constructing directly::

        # Enable everything registered
        cfg = ObfuscationConfig.all_enabled()

        # Enable a specific subset
        cfg = ObfuscationConfig.only("variable_renamer", "string_hex_encoder")

        # Start from all-enabled and exclude one
        cfg = ObfuscationConfig.all_enabled().without("string_hex_encoder")
    """

    enabled_techniques: frozenset[str]

    @classmethod
    def all_enabled(cls) -> ObfuscationConfig:
        from .techniques.registry import all_technique_names

        return cls(enabled_techniques=all_technique_names())

    @classmethod
    def only(cls, *names: str) -> ObfuscationConfig:
        return cls(enabled_techniques=frozenset(names))

    def without(self, *names: str) -> ObfuscationConfig:
        return ObfuscationConfig(
            enabled_techniques=self.enabled_techniques - frozenset(names)
        )

    def with_added(self, *names: str) -> ObfuscationConfig:
        return ObfuscationConfig(
            enabled_techniques=self.enabled_techniques | frozenset(names)
        )
