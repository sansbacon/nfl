"""Common model helpers for NFLverse datasets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NflverseRecordMeta:
    record_hash: str
    dataset: str
    loaded_at: str


COMMON_ENTITY_NAMES: tuple[str, ...] = (
    "players",
    "schedules",
    "ff_playerids",
)
