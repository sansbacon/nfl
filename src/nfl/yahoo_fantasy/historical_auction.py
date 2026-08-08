"""Historical auction value ingestion and reconciliation helpers."""

from __future__ import annotations

import contextlib
import hashlib
import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import polars as pl

from nfl.entity_standardization.normalize import (
    normalize_player_name,
    normalize_position,
    normalize_team_code,
)
from nfl.yahoo_fantasy.storage.iceberg import IcebergCatalogConfig


@dataclass(frozen=True, slots=True)
class HistoricalAuctionImportResult:
    raw: pl.DataFrame
    resolved: pl.DataFrame
    match_queue: pl.DataFrame


@dataclass(frozen=True, slots=True)
class HistoricalAuctionPersistResult:
    table_identifier: str
    rows_written: int


def _score_name_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return float(SequenceMatcher(None, left, right).ratio())


def _compact_name_key(value: str) -> str:
    """Build a punctuation/whitespace-insensitive key for name matching."""
    if not value:
        return ""
    return "".join(ch for ch in value if ch.isalnum())


def _name_parts(normalized_name: str) -> tuple[str, str]:
    tokens = [tok for tok in normalized_name.split(" ") if tok]
    if len(tokens) < 2:
        return "", ""
    return tokens[0], tokens[-1]


def _prefix_match(a: str, b: str, prefix_len: int = 3) -> bool:
    if len(a) < prefix_len or len(b) < prefix_len:
        return False
    return a[:prefix_len] == b[:prefix_len]


def _starts_with_team_phrase(raw_name: str, candidate_name: str) -> bool:
    if not raw_name or not candidate_name:
        return False
    if raw_name == candidate_name:
        return True
    return candidate_name.startswith(f"{raw_name} ")


def _hash_source_row(row: dict[str, Any]) -> str:
    payload = {
        "season": int(row.get("season") or 0),
        "pick_number": int(row.get("pick_number") or 0),
        "auction_price": float(row.get("auction_price") or 0.0),
        "team_raw": str(row.get("team_raw") or ""),
        "player_name_raw": str(row.get("player_name_raw") or ""),
        "position_raw": str(row.get("position_raw") or ""),
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_historical_auction_values(csv_path: str | Path) -> pl.DataFrame:
    """Load historical auction CSV into a normalized raw frame."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Historical auction CSV not found: {path}")

    df = pl.read_csv(path)
    rename_map = {
        "histi": "season",
        "Pick": "pick_number",
        "Salary": "auction_price",
        "Team": "team_raw",
        "Player": "player_name_raw",
        "Position": "position_raw",
        "Dollar_Rank": "dollar_rank",
        "Pos_Dollar_Rank": "position_dollar_rank",
    }

    missing = [name for name in rename_map if name not in df.columns]
    if missing:
        raise ValueError(f"Missing required historical auction columns: {missing}")

    out = (
        df.rename(rename_map)
        .with_columns(
            [
                pl.col("season").cast(pl.Int64, strict=False),
                pl.col("pick_number").cast(pl.Int64, strict=False),
                pl.col("auction_price").cast(pl.Float64, strict=False),
                pl.col("dollar_rank").cast(pl.Int64, strict=False),
                pl.col("position_dollar_rank").cast(pl.Int64, strict=False),
                pl.col("team_raw").cast(pl.Utf8, strict=False),
                pl.col("player_name_raw").cast(pl.Utf8, strict=False),
                pl.col("position_raw").cast(pl.Utf8, strict=False),
            ]
        )
        .with_columns(
            [
                pl.col("team_raw")
                .map_elements(normalize_team_code, return_dtype=pl.Utf8)
                .alias("team_normalized"),
                pl.col("player_name_raw")
                .map_elements(normalize_player_name, return_dtype=pl.Utf8)
                .alias("player_name_normalized"),
                pl.col("position_raw")
                .map_elements(normalize_position, return_dtype=pl.Utf8)
                .alias("position_normalized"),
            ]
        )
    )

    source_hashes = [_hash_source_row(row) for row in out.to_dicts()]
    out = out.with_columns(pl.Series("source_row_hash", source_hashes))
    return out


def resolve_historical_players(
    raw_df: pl.DataFrame,
    yahoo_player_df: pl.DataFrame,
    min_confidence: float = 0.97,
    review_confidence: float = 0.90,
) -> HistoricalAuctionImportResult:
    """Resolve historical player rows to Yahoo player identities."""
    required_player_cols = {"player_key", "player_id", "full_name", "display_position"}
    missing_player_cols = required_player_cols - set(yahoo_player_df.columns)
    if missing_player_cols:
        raise ValueError(f"yahoo_player_df missing columns: {sorted(missing_player_cols)}")

    players = yahoo_player_df.select(
        ["player_key", "player_id", "full_name", "display_position", "editorial_team_abbr"]
        if "editorial_team_abbr" in yahoo_player_df.columns
        else ["player_key", "player_id", "full_name", "display_position"]
    ).with_columns(
        [
            pl.col("full_name")
            .map_elements(normalize_player_name, return_dtype=pl.Utf8)
            .alias("full_name_normalized"),
            pl.col("display_position")
            .map_elements(normalize_position, return_dtype=pl.Utf8)
            .alias("display_position_normalized"),
            (
                pl.col("editorial_team_abbr").map_elements(
                    normalize_team_code, return_dtype=pl.Utf8
                )
                if "editorial_team_abbr" in yahoo_player_df.columns
                else pl.lit("")
            ).alias("team_normalized"),
            pl.col("full_name")
            .map_elements(normalize_player_name, return_dtype=pl.Utf8)
            .map_elements(_compact_name_key, return_dtype=pl.Utf8)
            .alias("full_name_compact"),
        ]
    )

    player_rows = players.to_dicts()
    last_name_name_keys_by_position: dict[tuple[str, str], set[str]] = {}
    for player in player_rows:
        player_name = str(player.get("full_name_normalized") or "")
        player_name_key = str(player.get("full_name_compact") or "")
        _, player_last = _name_parts(player_name)
        player_pos = str(player.get("display_position_normalized") or "")
        if not player_last or not player_pos or not player_name_key:
            continue
        key = (player_last, player_pos)
        names = last_name_name_keys_by_position.setdefault(key, set())
        names.add(player_name_key)

    resolved_rows: list[dict[str, Any]] = []
    queue_rows: list[dict[str, Any]] = []

    for row in raw_df.to_dicts():
        raw_name = str(row.get("player_name_normalized") or "")
        raw_name_compact = _compact_name_key(raw_name)
        raw_pos = str(row.get("position_normalized") or "")
        raw_team = str(row.get("team_normalized") or "")
        raw_first, raw_last = _name_parts(raw_name)
        is_defense_row = raw_pos == "DST"

        position_filtered_players = [
            player
            for player in player_rows
            if (not raw_pos) or str(player.get("display_position_normalized") or "") == raw_pos
        ]

        exact_matches = [
            player
            for player in position_filtered_players
            if (
                str(player.get("full_name_normalized") or "") == raw_name
                or str(player.get("full_name_compact") or "") == raw_name_compact
            )
        ]

        best: dict[str, Any] | None = None
        best_score = 0.0
        method = "unresolved"

        if exact_matches:
            best = exact_matches[0]
            best_score = 1.0
            method = "exact"
        else:
            if is_defense_row:
                if raw_team:
                    team_code_candidates = [
                        player
                        for player in position_filtered_players
                        if str(player.get("team_normalized") or "") == raw_team
                    ]
                    if team_code_candidates:
                        team_code_candidates = sorted(
                            team_code_candidates,
                            key=lambda p: (
                                int(p.get("game_id") or 0),
                                str(p.get("player_key") or ""),
                            ),
                            reverse=True,
                        )
                        best = team_code_candidates[0]
                        best_score = 0.99
                        method = "dst_team_code"

                dst_candidates = [
                    player
                    for player in position_filtered_players
                    if _starts_with_team_phrase(
                        raw_name,
                        str(player.get("full_name_normalized") or ""),
                    )
                ]
                if method != "dst_team_code" and len(dst_candidates) == 1:
                    best = dst_candidates[0]
                    best_score = 0.985
                    method = "dst_team_name"

            nickname_matches = [
                player
                for player in position_filtered_players
                if raw_last
                and raw_pos
                and str(player.get("display_position_normalized") or "") == raw_pos
                and _name_parts(str(player.get("full_name_normalized") or ""))[1] == raw_last
                and _prefix_match(
                    raw_first, _name_parts(str(player.get("full_name_normalized") or ""))[0]
                )
                and len(last_name_name_keys_by_position.get((raw_last, raw_pos), set())) == 1
            ]
            if nickname_matches:
                best = nickname_matches[0]
                best_score = 0.985
                method = "nickname_heuristic"

            for player in position_filtered_players:
                if method in {"nickname_heuristic", "dst_team_name", "dst_team_code"}:
                    break
                player_name = str(player.get("full_name_normalized") or "")
                player_name_compact = str(player.get("full_name_compact") or "")
                score = max(
                    _score_name_similarity(raw_name, player_name),
                    _score_name_similarity(raw_name_compact, player_name_compact),
                )

                player_pos = str(player.get("display_position_normalized") or "")
                if raw_pos and player_pos == raw_pos:
                    score += 0.02

                if score > best_score:
                    best_score = score
                    best = player
                    method = "fuzzy"

        status = "unresolved"
        if best is not None and best_score >= min_confidence:
            status = "resolved"
        elif best is not None and best_score >= review_confidence:
            status = "ambiguous"

        resolved_row = {
            "source_row_hash": row["source_row_hash"],
            "season": int(row.get("season") or 0),
            "pick_number": int(row.get("pick_number") or 0),
            "auction_price": float(row.get("auction_price") or 0.0),
            "team_raw": str(row.get("team_raw") or ""),
            "player_name_raw": str(row.get("player_name_raw") or ""),
            "position_raw": str(row.get("position_raw") or ""),
            "player_name_normalized": raw_name,
            "position_normalized": raw_pos,
            "team_normalized": raw_team,
            "yahoo_player_key": str(best.get("player_key") or "") if best is not None else "",
            "yahoo_player_id": int(best.get("player_id") or 0)
            if best is not None and best.get("player_id") is not None
            else None,
            "resolved_player_name": str(best.get("full_name") or "") if best is not None else "",
            "resolved_position": str(best.get("display_position") or "")
            if best is not None
            else "",
            "resolution_status": status,
            "resolution_confidence": round(float(best_score), 4),
            "resolution_method": method,
        }
        resolved_rows.append(resolved_row)

        if status in {"ambiguous", "unresolved"}:
            queue_rows.append(
                {
                    "source_row_hash": row["source_row_hash"],
                    "season": int(row.get("season") or 0),
                    "player_name_raw": str(row.get("player_name_raw") or ""),
                    "position_raw": str(row.get("position_raw") or ""),
                    "team_raw": str(row.get("team_raw") or ""),
                    "resolution_status": status,
                    "resolution_confidence": round(float(best_score), 4),
                    "candidate_player_key": str(best.get("player_key") or "")
                    if best is not None
                    else "",
                    "candidate_player_name": str(best.get("full_name") or "")
                    if best is not None
                    else "",
                    "candidate_position": str(best.get("display_position") or "")
                    if best is not None
                    else "",
                }
            )

    return HistoricalAuctionImportResult(
        raw=raw_df,
        resolved=pl.DataFrame(resolved_rows),
        match_queue=pl.DataFrame(queue_rows),
    )


def persist_historical_auction_tables(
    import_result: HistoricalAuctionImportResult,
    catalog_config: IcebergCatalogConfig | None = None,
    namespace: str = "yhnfl_manual",
    dry_run: bool = False,
    replace_existing: bool = True,
) -> list[HistoricalAuctionPersistResult]:
    """Persist historical auction tables to an independent Iceberg namespace."""
    if dry_run:
        return [
            HistoricalAuctionPersistResult(
                table_identifier=f"{namespace}.historical_auction_values_raw",
                rows_written=import_result.raw.height,
            ),
            HistoricalAuctionPersistResult(
                table_identifier=f"{namespace}.historical_auction_values_resolved",
                rows_written=import_result.resolved.height,
            ),
            HistoricalAuctionPersistResult(
                table_identifier=f"{namespace}.historical_auction_values_match_queue",
                rows_written=import_result.match_queue.height,
            ),
        ]

    cfg = catalog_config or IcebergCatalogConfig()

    try:
        from pyiceberg.catalog import load_catalog
        from pyiceberg.exceptions import NamespaceAlreadyExistsError, NoSuchTableError
    except ModuleNotFoundError as exc:
        raise RuntimeError("pyiceberg is required to persist historical auction tables") from exc

    catalog = load_catalog(
        cfg.catalog_name,
        type=cfg.catalog_type,
        uri=cfg.uri,
        warehouse=cfg.warehouse,
    )

    with contextlib.suppress(NamespaceAlreadyExistsError):
        catalog.create_namespace(namespace)

    targets: list[tuple[str, pl.DataFrame]] = [
        (f"{namespace}.historical_auction_values_raw", import_result.raw),
        (f"{namespace}.historical_auction_values_resolved", import_result.resolved),
        (f"{namespace}.historical_auction_values_match_queue", import_result.match_queue),
    ]

    results: list[HistoricalAuctionPersistResult] = []
    for table_identifier, frame in targets:
        if replace_existing:
            with contextlib.suppress(NoSuchTableError):
                catalog.drop_table(table_identifier)
            table = catalog.create_table(identifier=table_identifier, schema=frame.to_arrow().schema)
            if frame.height > 0:
                table.append(frame.to_arrow())
            results.append(
                HistoricalAuctionPersistResult(
                    table_identifier=table_identifier, rows_written=frame.height
                )
            )
            continue

        if frame.height == 0:
            results.append(
                HistoricalAuctionPersistResult(table_identifier=table_identifier, rows_written=0)
            )
            continue

        try:
            table = catalog.load_table(table_identifier)
        except NoSuchTableError:
            table = catalog.create_table(
                identifier=table_identifier, schema=frame.to_arrow().schema
            )

        table.append(frame.to_arrow())
        results.append(
            HistoricalAuctionPersistResult(
                table_identifier=table_identifier, rows_written=frame.height
            )
        )

    return results
