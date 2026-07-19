"""Shared entity standardization library."""

from nfl.entity_standardization.canonical import CanonicalRegistry, CanonicalRegistryLoader
from nfl.entity_standardization.pipeline import (
    EntityStandardizer,
    StandardizationConfig,
    StandardizationResult,
)

__all__ = [
    "canonical",
    "matching",
    "normalize",
    "overrides",
    "pipeline",
    "storage",
    "validation",
    "CanonicalRegistry",
    "CanonicalRegistryLoader",
    "EntityStandardizer",
    "StandardizationConfig",
    "StandardizationResult",
]
