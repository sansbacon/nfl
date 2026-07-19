"""Schema and quality validation for FantasyPros datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Literal, Mapping

from nfl.fantasypros_fantasy.models.nfl import NFL_CONTRACTS

SportCode = Literal["nfl"]


class ContractValidationError(ValueError):
    """Raised when a record or frame violates a contract."""


@dataclass(frozen=True, slots=True)
class EntityContract:
    name: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    primary_key: tuple[str, ...]

    @property
    def allowed_fields(self) -> set[str]:
        return set(self.required + self.optional)


COMMON_CONTRACTS: dict[str, EntityContract] = {
    "fp_player": EntityContract(
        name="fp_player",
        required=("fp_player_id", "full_name", "first_name", "last_name", "position", "team"),
        optional=(),
        primary_key=("fp_player_id",),
    ),
    "fp_adp_snapshot": EntityContract(
        name="fp_adp_snapshot",
        required=(
            "fp_player_id",
            "season",
            "rank",
            "adp",
            "effective_date",
            "is_current",
        ),
        optional=(
            "adp_espn",
            "adp_sleeper",
            "adp_cbs",
            "adp_nfl",
            "adp_rtsports",
            "adp_fantrax",
            "adp_realtime",
            "adp_formatted",
            "high",
            "low",
            "stdev",
            "bye_week",
            "end_date",
        ),
        primary_key=("fp_player_id", "season", "effective_date"),
    ),
    "fp_yahoo_player_map": EntityContract(
        name="fp_yahoo_player_map",
        required=("fp_player_id", "yahoo_player_id", "match_method", "matched_at"),
        optional=(),
        primary_key=("fp_player_id", "yahoo_player_id"),
    ),
}


def _build_contracts(raw_contracts: Mapping[str, Mapping[str, tuple[str, ...]]]) -> dict[str, EntityContract]:
    contracts: dict[str, EntityContract] = {}
    for name, cfg in raw_contracts.items():
        contracts[name] = EntityContract(
            name=name,
            required=cfg["required"],
            optional=cfg["optional"],
            primary_key=cfg["primary_key"],
        )
    return contracts


SPORT_CONTRACTS: dict[SportCode, dict[str, EntityContract]] = {
    "nfl": _build_contracts(NFL_CONTRACTS),
}


def get_contract(entity: str, sport: SportCode | None = None) -> EntityContract:
    if sport is not None:
        scoped = SPORT_CONTRACTS.get(sport, {})
        if entity in scoped:
            return scoped[entity]
    if entity in COMMON_CONTRACTS:
        return COMMON_CONTRACTS[entity]
    raise KeyError(f"Unknown entity '{entity}'")


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


def validate_records(
    records: Iterable[Mapping[str, Any]],
    contract: EntityContract,
    allow_extra_fields: bool = True,
) -> int:
    count = 0
    for idx, record in enumerate(records):
        try:
            validate_record(record, contract, allow_extra_fields=allow_extra_fields)
        except ContractValidationError as exc:
            raise ContractValidationError(f"{contract.name}: row {idx}: {exc}") from exc
        count += 1
    return count


def validate_primary_key_uniqueness(records: Iterable[Mapping[str, Any]], contract: EntityContract) -> None:
    seen: set[tuple[Any, ...]] = set()
    for idx, record in enumerate(records):
        key = tuple(record.get(field) for field in contract.primary_key)
        if None in key:
            missing = [field for field, value in zip(contract.primary_key, key, strict=True) if value is None]
            raise ContractValidationError(
                f"{contract.name}: row {idx}: primary key field(s) None: {', '.join(missing)}"
            )
        if key in seen:
            raise ContractValidationError(f"{contract.name}: row {idx}: duplicate primary key {key}")
        seen.add(key)


def validate_polars_frame(frame: Any, contract: EntityContract, allow_extra_fields: bool = True) -> None:
    columns = set(getattr(frame, "columns", []))
    if not columns:
        raise ContractValidationError(f"{contract.name}: frame has no columns")

    missing = [f for f in contract.required if f not in columns]
    if missing:
        raise ContractValidationError(
            f"{contract.name}: frame missing required columns: {', '.join(missing)}"
        )

    if not allow_extra_fields:
        extras = columns - contract.allowed_fields
        if extras:
            raise ContractValidationError(
                f"{contract.name}: frame has unexpected columns: {', '.join(sorted(extras))}"
            )

    null_count = getattr(frame, "null_count", None)
    if callable(null_count):
        stats = null_count().to_dicts()[0]
        offenders = [field for field in contract.required if stats.get(field, 0) > 0]
        if offenders:
            raise ContractValidationError(
                f"{contract.name}: required columns contain nulls: {', '.join(offenders)}"
            )


def validate(records: Iterable[Mapping[str, Any]], entity: str, sport: SportCode | None = None) -> int:
    contract = get_contract(entity=entity, sport=sport)
    rows = list(records)
    count = validate_records(rows, contract)
    validate_primary_key_uniqueness(rows, contract)
    return count
