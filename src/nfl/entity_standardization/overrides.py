"""Manual override helpers."""

from __future__ import annotations

from typing import Any


def build_override_index(overrides: list[dict[str, Any]] | None) -> dict[tuple[str, str], dict[str, Any]]:
    if not overrides:
        return {}
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for row in overrides:
        source_system = str(row.get("source_system") or "").lower()
        source_entity_id = str(row.get("source_entity_id") or "")
        if not source_system or not source_entity_id:
            continue
        index[(source_system, source_entity_id)] = row
    return index
