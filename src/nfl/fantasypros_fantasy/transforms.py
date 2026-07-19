"""Polars transformation interfaces for FantasyPros datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import polars as pl

from nfl.fantasypros_fantasy.validation import (
    ContractValidationError,
    get_contract,
    validate,
    validate_polars_frame,
)


class TransformValidationError(ValueError):
    """Raised when transformation outputs fail quality checks."""


@dataclass(frozen=True, slots=True)
class TransformResult:
    frames: dict[str, pl.DataFrame]


_INT_COLUMNS = {
    "season",
    "rank",
    "high",
    "low",
    "bye_week",
    "yahoo_player_id",
}
_FLOAT_COLUMNS = {
    "adp",
    "adp_espn",
    "adp_sleeper",
    "adp_cbs",
    "adp_nfl",
    "adp_rtsports",
    "adp_fantrax",
    "adp_realtime",
    "stdev",
}
_BOOL_COLUMNS = {"is_current"}


def _empty_frame_for_contract(required: tuple[str, ...], optional: tuple[str, ...]) -> pl.DataFrame:
    return pl.DataFrame({col: [] for col in list(required + optional)})


def _coerce_frame_types(frame: pl.DataFrame) -> pl.DataFrame:
    casts: list[pl.Expr] = []
    for col in frame.columns:
        if col in _INT_COLUMNS:
            casts.append(pl.col(col).cast(pl.Int64, strict=False))
        elif col in _FLOAT_COLUMNS:
            casts.append(pl.col(col).cast(pl.Float64, strict=False))
        elif col in _BOOL_COLUMNS:
            casts.append(pl.col(col).cast(pl.Boolean, strict=False))
    return frame.with_columns(casts) if casts else frame


def _sorted_by_primary_key(frame: pl.DataFrame, primary_key: tuple[str, ...]) -> pl.DataFrame:
    keys = [k for k in primary_key if k in frame.columns]
    return frame.sort(keys) if keys else frame


def transform_entity(
    records: Iterable[Mapping[str, Any]],
    entity: str,
    sport: str | None = None,
    keep_extra_fields: bool = False,
) -> pl.DataFrame:
    contract = get_contract(entity=entity, sport=sport)  # type: ignore[arg-type]
    records_list = list(records)
    try:
        validate(records_list, entity=entity, sport=sport)  # type: ignore[arg-type]
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    if not records_list:
        return _coerce_frame_types(_empty_frame_for_contract(contract.required, contract.optional))

    if keep_extra_fields:
        frame = pl.DataFrame(records_list)
    else:
        allowed = list(contract.required + contract.optional)
        normalized = [{field: row.get(field) for field in allowed} for row in records_list]
        frame = pl.DataFrame(normalized)

    frame = _coerce_frame_types(frame)
    try:
        validate_polars_frame(frame, contract, allow_extra_fields=keep_extra_fields)
    except ContractValidationError as exc:
        raise TransformValidationError(str(exc)) from exc

    return _sorted_by_primary_key(frame, contract.primary_key)


def transform_nfl(
    adp_snapshots: Iterable[Mapping[str, Any]] | None = None,
    yahoo_player_map: Iterable[Mapping[str, Any]] | None = None,
) -> TransformResult:
    return TransformResult(
        frames={
            "fp_adp_snapshot": transform_entity(adp_snapshots or [], entity="fp_adp_snapshot", sport="nfl"),
            "fp_yahoo_player_map": transform_entity(yahoo_player_map or [], entity="fp_yahoo_player_map", sport="nfl"),
        }
    )


def transform(
    common_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
    nfl_entities: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, pl.DataFrame]:
    common_entities = common_entities or {}
    nfl_entities = nfl_entities or {}

    common_frames = {
        "fp_player": transform_entity(common_entities.get("fp_player", []), entity="fp_player")
    }

    nfl = transform_nfl(
        adp_snapshots=nfl_entities.get("fp_adp_snapshot", []),
        yahoo_player_map=nfl_entities.get("fp_yahoo_player_map", []),
    )

    return {
        **common_frames,
        **{f"nfl_{name}": frame for name, frame in nfl.frames.items()},
    }
