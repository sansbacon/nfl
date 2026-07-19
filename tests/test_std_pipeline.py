from __future__ import annotations

from datetime import datetime, timezone

from nfl.entity_standardization.canonical import CanonicalRegistry
from nfl.entity_standardization.pipeline import EntityStandardizer, StandardizationConfig


def _registry() -> CanonicalRegistry:
    return CanonicalRegistry(
        players=[
            {
                "canonical_player_id": "P1",
                "display_name": "Austin Ekeler",
                "first_name": "Austin",
                "last_name": "Ekeler",
                "current_team": "LAC",
                "primary_position": "RB",
                "aliases": ["AUSTIN EKELER"],
                "source_version": "v1",
                "cross_source_ids": {"yahoo": "1001"},
            }
        ],
        teams=[
            {
                "canonical_team_id": "LAC",
                "canonical_team_name": "LAC",
                "canonical_team_abbr": "LAC",
                "aliases": ["LAC", "SAN DIEGO"],
                "source_version": "v1",
                "team_code_authority": "load_schedules",
            }
        ],
        positions=[
            {"canonical_position_id": "RB", "canonical_position_code": "RB", "aliases": ["RB", "HB", "FB"]}
        ],
        source_to_canonical_map=[
            {
                "source_system": "yahoo",
                "source_entity_id": "1001",
                "canonical_player_id": "P1",
                "provenance": "nflreadpy.load_ff_playerids",
                "valid_from": None,
                "valid_to": None,
            }
        ],
    )


def test_standardize_batch_writes_queue_and_rescues_for_low_confidence() -> None:
    cfg = StandardizationConfig(
        auto_accept_thresholds={"default": {"player": 0.99, "team": 0.99, "position": 1.0}}
    )
    standardizer = EntityStandardizer(config=cfg, canonical_registry=_registry())

    result = standardizer.standardize_batch(
        [
            {
                "source_system": "yahoo",
                "source_entity_id": "1001",
                "raw_player_name": "Austin Ekeler",
                "raw_team_name": "LAC",
                "raw_position": "RB",
                "season": 2025,
            },
            {
                "source_system": "fantasypros",
                "source_entity_id": "unknown",
                "raw_player_name": "Mystery Player",
                "raw_team_name": "LAC",
                "raw_position": "WR",
                "season": 2025,
            },
        ]
    )

    assert len(result.standardized_records) == 2
    assert result.tables["std_match_queue"].height == 1
    assert result.tables["std_rescued_records"].height == 1
    assert result.tables["std_match_queue_open"].height == 1


def test_standardize_batch_uses_manual_override() -> None:
    overrides = [
        {
            "source_system": "fantasypros",
            "source_entity_id": "fp_1",
            "canonical_player_id": "P1",
            "canonical_team_id": "LAC",
            "canonical_position_code": "RB",
            "approved_by": "tester",
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "notes": "manual",
        }
    ]
    standardizer = EntityStandardizer(canonical_registry=_registry(), manual_overrides=overrides)
    result = standardizer.standardize_batch(
        [
            {
                "source_system": "fantasypros",
                "source_entity_id": "fp_1",
                "raw_player_name": "Any Name",
                "raw_team_name": "Any Team",
                "raw_position": "HB",
                "season": 2025,
            }
        ]
    )

    row = result.standardized_records[0]
    assert row["match_method_player"] == "override"
    assert row["canonical_player_id"] == "P1"
    assert result.tables["std_match_queue"].height == 0
    assert result.tables["std_manual_overrides"].height == 1
