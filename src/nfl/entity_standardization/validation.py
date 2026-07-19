"""Contracts and validation utilities for standardization tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class ContractValidationError(ValueError):
    """Raised when records violate table contracts."""


@dataclass(frozen=True, slots=True)
class EntityContract:
    name: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    primary_key: tuple[str, ...]

    @property
    def allowed_fields(self) -> set[str]:
        return set(self.required + self.optional)


STANDARDIZATION_CONTRACTS: dict[str, EntityContract] = {
    "std_canonical_players": EntityContract(
        name="std_canonical_players",
        required=(
            "canonical_player_id",
            "display_name",
            "first_name",
            "last_name",
            "current_team",
            "primary_position",
            "aliases",
            "cross_source_ids",
            "source_version",
        ),
        optional=(),
        primary_key=("canonical_player_id",),
    ),
    "std_canonical_teams": EntityContract(
        name="std_canonical_teams",
        required=(
            "canonical_team_id",
            "canonical_team_name",
            "canonical_team_abbr",
            "aliases",
            "source_version",
            "team_code_authority",
        ),
        optional=(),
        primary_key=("canonical_team_id",),
    ),
    "std_canonical_positions": EntityContract(
        name="std_canonical_positions",
        required=("canonical_position_id", "canonical_position_code", "aliases"),
        optional=(),
        primary_key=("canonical_position_id",),
    ),
    "std_source_to_canonical_map": EntityContract(
        name="std_source_to_canonical_map",
        required=(
            "source_system",
            "source_entity_id",
            "canonical_player_id",
            "provenance",
        ),
        optional=("valid_from", "valid_to"),
        primary_key=("source_system", "source_entity_id"),
    ),
    "std_match_queue": EntityContract(
        name="std_match_queue",
        required=(
            "queue_id",
            "source_system",
            "source_entity_id",
            "raw_player_name",
            "raw_team_name",
            "raw_position",
            "reason_code",
            "candidate_json",
            "queue_status",
            "priority",
            "created_at",
        ),
        optional=(
            "assigned_to",
            "review_notes",
            "resolved_at",
            "resolved_by",
            "resolution_action",
        ),
        primary_key=("queue_id",),
    ),
    "std_rescued_records": EntityContract(
        name="std_rescued_records",
        required=(
            "rescue_id",
            "source_system",
            "source_entity_id",
            "raw_payload_json",
            "reason_code",
            "created_at",
            "replay_status",
        ),
        optional=("resolved_by_queue_id",),
        primary_key=("rescue_id",),
    ),
    "std_standardized_outputs": EntityContract(
        name="std_standardized_outputs",
        required=(
            "source_system",
            "source_entity_id",
            "canonical_player_id",
            "canonical_team_id",
            "canonical_position_code",
            "standardized_player_name",
            "standardized_team_name",
            "standardized_position",
            "player_confidence",
            "team_confidence",
            "position_confidence",
            "match_method_player",
            "match_method_team",
            "match_method_position",
            "explanation_json",
            "needs_review",
            "rescued",
        ),
        optional=(),
        primary_key=("source_system", "source_entity_id"),
    ),
    "std_match_queue_open": EntityContract(
        name="std_match_queue_open",
        required=(
            "queue_id",
            "source_system",
            "source_entity_id",
            "queue_status",
            "priority",
            "created_at",
        ),
        optional=("assigned_to",),
        primary_key=("queue_id",),
    ),
    "std_match_queue_history": EntityContract(
        name="std_match_queue_history",
        required=(
            "queue_id",
            "source_system",
            "source_entity_id",
            "queue_status",
            "created_at",
            "resolved_at",
            "resolution_action",
        ),
        optional=("resolved_by", "review_notes"),
        primary_key=("queue_id",),
    ),
    "std_manual_overrides": EntityContract(
        name="std_manual_overrides",
        required=(
            "source_system",
            "source_entity_id",
            "canonical_player_id",
            "canonical_team_id",
            "canonical_position_code",
            "approved_by",
            "approved_at",
        ),
        optional=("notes",),
        primary_key=("source_system", "source_entity_id"),
    ),
}


def get_contract(entity: str) -> EntityContract:
    if entity not in STANDARDIZATION_CONTRACTS:
        raise KeyError(f"Unknown standardization entity '{entity}'")
    return STANDARDIZATION_CONTRACTS[entity]


def validate_record(record: Mapping[str, Any], contract: EntityContract, allow_extra_fields: bool = True) -> None:
    missing = [f for f in contract.required if f not in record]
    if missing:
        raise ContractValidationError(f"{contract.name}: missing required fields: {', '.join(missing)}")

    null_required = [f for f in contract.required if record.get(f) is None]
    if null_required:
        raise ContractValidationError(
            f"{contract.name}: required fields cannot be None: {', '.join(null_required)}"
        )

    if not allow_extra_fields:
        extras = set(record.keys()) - contract.allowed_fields
        if extras:
            raise ContractValidationError(
                f"{contract.name}: unexpected fields: {', '.join(sorted(extras))}"
            )


def validate(records: Iterable[Mapping[str, Any]], entity: str) -> int:
    contract = get_contract(entity)
    seen: set[tuple[Any, ...]] = set()
    count = 0

    for idx, record in enumerate(records):
        validate_record(record, contract)
        key = tuple(record.get(field) for field in contract.primary_key)
        if None in key:
            raise ContractValidationError(f"{contract.name}: row {idx}: primary key contains None")
        if key in seen:
            raise ContractValidationError(f"{contract.name}: row {idx}: duplicate primary key {key}")
        seen.add(key)
        count += 1

    return count
