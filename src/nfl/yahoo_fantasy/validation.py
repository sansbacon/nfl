"""Schema and quality validation interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Literal

from nfl.yahoo_fantasy.models.nba import NBA_CONTRACTS
from nfl.yahoo_fantasy.models.nfl import NFL_CONTRACTS

SportCode = Literal["nfl", "nba"]


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
    "league": EntityContract(
        name="league",
        required=(
            "league_key",
            "league_id",
            "game_id",
            "game_code",
            "season",
            "league_name",
            "scoring_type",
            "league_type",
        ),
        optional=("num_teams",),
        primary_key=("league_key",),
    ),
    "team": EntityContract(
        name="team",
        required=("team_key", "league_key", "team_id", "team_name", "owner_name"),
        optional=("draft_position",),
        primary_key=("team_key",),
    ),
    "player": EntityContract(
        name="player",
        required=(
            "player_key",
            "player_id",
            "game_id",
            "full_name",
            "display_position",
        ),
        optional=("editorial_team_abbr",),
        primary_key=("player_key",),
    ),
    "draft_pick": EntityContract(
        name="draft_pick",
        required=(
            "league_key",
            "season",
            "team_key",
            "player_key",
            "pick_number",
            "round_number",
        ),
        optional=("cost",),
        primary_key=("league_key", "season", "pick_number"),
    ),
    "transaction": EntityContract(
        name="transaction",
        required=(
            "transaction_key",
            "league_key",
            "season",
            "transaction_type",
            "status",
            "player_key",
        ),
        optional=("source_team_key", "destination_team_key"),
        primary_key=("transaction_key", "player_key"),
    ),
    "stat_category": EntityContract(
        name="stat_category",
        required=("game_id", "stat_id", "display_name", "name"),
        optional=(),
        primary_key=("game_id", "stat_id"),
    ),
    "scoring_rule": EntityContract(
        name="scoring_rule",
        required=("league_key", "season", "stat_id", "points_per_unit"),
        optional=("bonus_target", "bonus_points"),
        primary_key=("league_key", "season", "stat_id"),
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
    "nba": _build_contracts(NBA_CONTRACTS),
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
