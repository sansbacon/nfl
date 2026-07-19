"""Schema and quality validation for NFLverse wrapper datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from nfl.nflverse_fantasy.models.nfl import NFL_CONTRACTS


class ContractValidationError(ValueError):
    """Raised when records or frames violate contracts."""


@dataclass(frozen=True, slots=True)
class EntityContract:
    name: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    primary_key: tuple[str, ...]

    @property
    def allowed_fields(self) -> set[str]:
        return set(self.required + self.optional)


def _build_contracts(raw: Mapping[str, Mapping[str, tuple[str, ...]]]) -> dict[str, EntityContract]:
    return {
        name: EntityContract(
            name=name,
            required=cfg["required"],
            optional=cfg["optional"],
            primary_key=cfg["primary_key"],
        )
        for name, cfg in raw.items()
    }


CONTRACTS = _build_contracts(NFL_CONTRACTS)


def get_contract(entity: str) -> EntityContract:
    if entity not in CONTRACTS:
        raise KeyError(f"Unknown entity '{entity}'")
    return CONTRACTS[entity]


def validate_record(record: Mapping[str, Any], contract: EntityContract, allow_extra_fields: bool = True) -> None:
    missing = [field for field in contract.required if field not in record]
    if missing:
        raise ContractValidationError(f"{contract.name}: missing required fields: {', '.join(missing)}")

    null_required = [field for field in contract.required if record.get(field) is None]
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


def validate_polars_frame(frame: Any, contract: EntityContract) -> None:
    columns = set(getattr(frame, "columns", []))
    missing = [field for field in contract.required if field not in columns]
    if missing:
        raise ContractValidationError(
            f"{contract.name}: frame missing required columns: {', '.join(missing)}"
        )
