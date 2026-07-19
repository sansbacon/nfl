"""Entity standardization orchestration service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import polars as pl

from nfl.entity_standardization.canonical import CanonicalRegistry, CanonicalRegistryLoader
from nfl.entity_standardization.matching import match_player, match_position, match_team
from nfl.entity_standardization.overrides import build_override_index
from nfl.entity_standardization.storage import (
    StandardizationIcebergNamespaceConfig,
    StandardizationIcebergWriteResult,
    persist_to_iceberg,
    persist_with_polars,
)
from nfl.entity_standardization.validation import validate


@dataclass(frozen=True, slots=True)
class StandardizationConfig:
    auto_accept_thresholds: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "default": {"player": 0.97, "team": 0.995, "position": 1.0}
        }
    )
    persist_tables: bool = False
    polars_output_dir: str | Path = "./output/standardization"
    polars_file_format: str = "parquet"
    iceberg_enabled: bool = False
    iceberg_dry_run: bool = True
    iceberg_idempotency_store: str | Path = ".iceberg/std_write_log.json"
    iceberg_namespaces: StandardizationIcebergNamespaceConfig = field(
        default_factory=StandardizationIcebergNamespaceConfig
    )


@dataclass(frozen=True, slots=True)
class StandardizationResult:
    standardized_records: list[dict[str, Any]]
    tables: dict[str, pl.DataFrame]
    polars_outputs: dict[str, Path]
    iceberg_outputs: list[StandardizationIcebergWriteResult]


class EntityStandardizer:
    def __init__(
        self,
        config: StandardizationConfig | None = None,
        canonical_registry: CanonicalRegistry | None = None,
        manual_overrides: list[dict[str, Any]] | None = None,
        source_map: list[dict[str, Any]] | None = None,
    ) -> None:
        self.config = config or StandardizationConfig()
        self.registry = canonical_registry or CanonicalRegistryLoader().load_registry()
        self.manual_overrides = list(manual_overrides or [])
        self.override_index = build_override_index(manual_overrides)
        self.source_map_index: dict[tuple[str, str], str] = {}

        for row in (source_map or []) + self.registry.source_to_canonical_map:
            source = str(row.get("source_system") or "").lower()
            source_entity_id = str(row.get("source_entity_id") or "")
            canonical_player_id = str(row.get("canonical_player_id") or "")
            if source and source_entity_id and canonical_player_id:
                self.source_map_index[(source, source_entity_id)] = canonical_player_id

        self.allowed_positions = {
            str(row.get("canonical_position_code") or "")
            for row in self.registry.positions
            if row.get("canonical_position_code")
        }

    def _threshold(self, source_system: str, entity: str) -> float:
        source_cfg = self.config.auto_accept_thresholds.get(source_system, {})
        default_cfg = self.config.auto_accept_thresholds.get("default", {})
        return float(source_cfg.get(entity, default_cfg.get(entity, 1.0)))

    def standardize_position(self, raw_position: str, source_system: str = "default") -> dict[str, Any]:
        decision = match_position(raw_position, self.allowed_positions)
        threshold = self._threshold(source_system, "position")
        accepted = decision.confidence >= threshold
        return {
            "canonical_position_code": decision.canonical_value if accepted else "",
            "position_confidence": decision.confidence,
            "match_method_position": decision.method if accepted else "unresolved",
            "needs_review": not accepted,
        }

    def standardize_team_name(self, raw_team_name: str, source_system: str = "default") -> dict[str, Any]:
        decision = match_team(raw_team_name, self.registry.teams)
        threshold = self._threshold(source_system, "team")
        accepted = decision.confidence >= threshold
        return {
            "canonical_team_id": decision.canonical_value if accepted else "",
            "team_confidence": decision.confidence,
            "match_method_team": decision.method if accepted else "unresolved",
            "needs_review": not accepted,
        }

    def standardize_player_name(
        self,
        raw_player_name: str,
        canonical_team_id: str,
        canonical_position_code: str,
        source_system: str = "default",
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        decision, candidates = match_player(
            raw_player_name=raw_player_name,
            canonical_players=self.registry.players,
            canonical_team_id=canonical_team_id,
            canonical_position_code=canonical_position_code,
        )
        threshold = self._threshold(source_system, "player")
        accepted = decision.confidence >= threshold
        return (
            {
                "canonical_player_id": decision.canonical_value if accepted else "",
                "player_confidence": decision.confidence,
                "match_method_player": decision.method if accepted else "unresolved",
                "needs_review": not accepted,
            },
            candidates,
        )

    def standardize_record(self, record: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
        source_system = str(record.get("source_system") or "").lower() or "default"
        source_entity_id = str(record.get("source_entity_id") or "")
        raw_player_name = str(record.get("raw_player_name") or "")
        raw_team_name = str(record.get("raw_team_name") or "")
        raw_position = str(record.get("raw_position") or "")

        override = self.override_index.get((source_system, source_entity_id))
        if override is not None:
            standardized = {
                "source_system": source_system,
                "source_entity_id": source_entity_id,
                "canonical_player_id": str(override.get("canonical_player_id") or ""),
                "canonical_team_id": str(override.get("canonical_team_id") or ""),
                "canonical_position_code": str(override.get("canonical_position_code") or ""),
                "standardized_player_name": raw_player_name,
                "standardized_team_name": raw_team_name,
                "standardized_position": raw_position,
                "player_confidence": 1.0,
                "team_confidence": 1.0,
                "position_confidence": 1.0,
                "match_method_player": "override",
                "match_method_team": "override",
                "match_method_position": "override",
                "explanation_json": json.dumps({"reason": "manual_override"}),
                "needs_review": False,
                "rescued": False,
            }
            return standardized, None, None, {
                "source_system": source_system,
                "source_entity_id": source_entity_id,
                "canonical_player_id": standardized["canonical_player_id"],
                "provenance": "manual_override",
                "valid_from": None,
                "valid_to": None,
            }

        team_result = self.standardize_team_name(raw_team_name, source_system)
        position_result = self.standardize_position(raw_position, source_system)

        mapped_player_id = self.source_map_index.get((source_system, source_entity_id), "")
        candidates: list[dict[str, Any]] = []
        if mapped_player_id:
            player_result = {
                "canonical_player_id": mapped_player_id,
                "player_confidence": 1.0,
                "match_method_player": "source_map",
                "needs_review": False,
            }
        else:
            player_result, candidates = self.standardize_player_name(
                raw_player_name=raw_player_name,
                canonical_team_id=team_result["canonical_team_id"],
                canonical_position_code=position_result["canonical_position_code"],
                source_system=source_system,
            )

        needs_review = bool(team_result["needs_review"] or position_result["needs_review"] or player_result["needs_review"])

        standardized = {
            "source_system": source_system,
            "source_entity_id": source_entity_id,
            "canonical_player_id": player_result["canonical_player_id"],
            "canonical_team_id": team_result["canonical_team_id"],
            "canonical_position_code": position_result["canonical_position_code"],
            "standardized_player_name": raw_player_name,
            "standardized_team_name": team_result["canonical_team_id"] or raw_team_name,
            "standardized_position": position_result["canonical_position_code"] or raw_position,
            "player_confidence": float(player_result["player_confidence"]),
            "team_confidence": float(team_result["team_confidence"]),
            "position_confidence": float(position_result["position_confidence"]),
            "match_method_player": player_result["match_method_player"],
            "match_method_team": team_result["match_method_team"],
            "match_method_position": position_result["match_method_position"],
            "explanation_json": json.dumps(
                {
                    "raw_player_name": raw_player_name,
                    "raw_team_name": raw_team_name,
                    "raw_position": raw_position,
                    "player_candidates": candidates,
                },
                default=str,
            ),
            "needs_review": needs_review,
            "rescued": needs_review,
        }

        queue_row = None
        rescue_row = None
        mapping_row = None

        if needs_review:
            now = datetime.now(timezone.utc).isoformat()
            queue_id = hashlib.sha256(f"{source_system}|{source_entity_id}|{raw_player_name}|{raw_team_name}|{raw_position}".encode("utf-8")).hexdigest()
            queue_row = {
                "queue_id": queue_id,
                "source_system": source_system,
                "source_entity_id": source_entity_id,
                "raw_player_name": raw_player_name,
                "raw_team_name": raw_team_name,
                "raw_position": raw_position,
                "reason_code": "low_confidence_or_unresolved",
                "candidate_json": standardized["explanation_json"],
                "queue_status": "new",
                "assigned_to": None,
                "priority": "high",
                "review_notes": None,
                "created_at": now,
                "resolved_at": None,
                "resolved_by": None,
                "resolution_action": None,
            }
            rescue_row = {
                "rescue_id": queue_id,
                "source_system": source_system,
                "source_entity_id": source_entity_id,
                "raw_payload_json": json.dumps(record, default=str),
                "reason_code": "needs_review",
                "created_at": now,
                "replay_status": "pending",
                "resolved_by_queue_id": None,
            }
        elif standardized["canonical_player_id"] and source_entity_id:
            mapping_row = {
                "source_system": source_system,
                "source_entity_id": source_entity_id,
                "canonical_player_id": standardized["canonical_player_id"],
                "provenance": standardized["match_method_player"],
                "valid_from": None,
                "valid_to": None,
            }

        return standardized, queue_row, rescue_row, mapping_row

    def _build_tables(
        self,
        standardized_rows: list[dict[str, Any]],
        queue_rows: list[dict[str, Any]],
        rescue_rows: list[dict[str, Any]],
        mapping_rows: list[dict[str, Any]],
    ) -> dict[str, pl.DataFrame]:
        deduped_mappings: list[dict[str, Any]] = []
        seen_map_keys: set[tuple[str, str]] = set()
        for row in mapping_rows:
            key = (str(row.get("source_system") or ""), str(row.get("source_entity_id") or ""))
            if key in seen_map_keys:
                continue
            seen_map_keys.add(key)
            deduped_mappings.append(row)

        canonical_players = self.registry.players
        for row in canonical_players:
            row.setdefault("cross_source_ids", {})
        validate(canonical_players, "std_canonical_players")
        validate(self.registry.teams, "std_canonical_teams")
        validate(self.registry.positions, "std_canonical_positions")
        validate(deduped_mappings or [], "std_source_to_canonical_map")
        validate(queue_rows or [], "std_match_queue")
        validate(rescue_rows or [], "std_rescued_records")
        validate(standardized_rows or [], "std_standardized_outputs")

        queue_open = [
            {
                "queue_id": row["queue_id"],
                "source_system": row["source_system"],
                "source_entity_id": row["source_entity_id"],
                "queue_status": row["queue_status"],
                "priority": row["priority"],
                "created_at": row["created_at"],
                "assigned_to": row.get("assigned_to"),
            }
            for row in queue_rows
            if row.get("queue_status") in {"new", "in_review"}
        ]
        queue_history = [
            {
                "queue_id": row["queue_id"],
                "source_system": row["source_system"],
                "source_entity_id": row["source_entity_id"],
                "queue_status": row["queue_status"],
                "created_at": row["created_at"],
                "resolved_at": row.get("resolved_at") or "",
                "resolution_action": row.get("resolution_action") or "",
                "resolved_by": row.get("resolved_by"),
                "review_notes": row.get("review_notes"),
            }
            for row in queue_rows
            if row.get("queue_status") not in {"new", "in_review"}
        ]

        validate(queue_open or [], "std_match_queue_open")
        validate(queue_history or [], "std_match_queue_history")

        manual_overrides = self.manual_overrides
        validate(manual_overrides, "std_manual_overrides")

        return {
            "std_canonical_players": pl.DataFrame(canonical_players),
            "std_canonical_teams": pl.DataFrame(self.registry.teams),
            "std_canonical_positions": pl.DataFrame(self.registry.positions),
            "std_source_to_canonical_map": pl.DataFrame(deduped_mappings),
            "std_match_queue": pl.DataFrame(queue_rows),
            "std_rescued_records": pl.DataFrame(rescue_rows),
            "std_standardized_outputs": pl.DataFrame(standardized_rows),
            "std_match_queue_open": pl.DataFrame(queue_open),
            "std_match_queue_history": pl.DataFrame(queue_history),
            "std_manual_overrides": pl.DataFrame(manual_overrides),
        }

    def standardize_batch(self, records: list[dict[str, Any]]) -> StandardizationResult:
        standardized_rows: list[dict[str, Any]] = []
        queue_rows: list[dict[str, Any]] = []
        rescue_rows: list[dict[str, Any]] = []
        mapping_rows: list[dict[str, Any]] = list(self.registry.source_to_canonical_map)

        for record in records:
            standardized, queue_row, rescue_row, mapping_row = self.standardize_record(record)
            standardized_rows.append(standardized)
            if queue_row is not None:
                queue_rows.append(queue_row)
            if rescue_row is not None:
                rescue_rows.append(rescue_row)
            if mapping_row is not None:
                mapping_rows.append(mapping_row)

        tables = self._build_tables(standardized_rows, queue_rows, rescue_rows, mapping_rows)

        polars_outputs: dict[str, Path] = {}
        iceberg_outputs: list[StandardizationIcebergWriteResult] = []

        if self.config.persist_tables:
            polars_outputs = persist_with_polars(
                tables,
                output_dir=self.config.polars_output_dir,
                file_format=self.config.polars_file_format,
            )

            if self.config.iceberg_enabled:
                iceberg_outputs = persist_to_iceberg(
                    tables,
                    namespace_config=self.config.iceberg_namespaces,
                    idempotency_store_path=self.config.iceberg_idempotency_store,
                    dry_run=self.config.iceberg_dry_run,
                )

        return StandardizationResult(
            standardized_records=standardized_rows,
            tables=tables,
            polars_outputs=polars_outputs,
            iceberg_outputs=iceberg_outputs,
        )
