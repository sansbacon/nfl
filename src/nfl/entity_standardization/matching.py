"""Matching utilities for canonical resolution."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from nfl.entity_standardization.normalize import normalize_player_name, normalize_position, normalize_team_code


@dataclass(frozen=True, slots=True)
class MatchDecision:
    canonical_value: str
    confidence: float
    method: str
    evidence: dict[str, Any]


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return float(SequenceMatcher(None, a, b).ratio())


def match_position(raw_position: str, allowed_positions: set[str]) -> MatchDecision:
    normalized = normalize_position(raw_position)
    if normalized in allowed_positions:
        return MatchDecision(canonical_value=normalized, confidence=1.0, method="alias", evidence={"raw": raw_position})
    return MatchDecision(canonical_value="", confidence=0.0, method="unresolved", evidence={"raw": raw_position})


def match_team(raw_team: str, canonical_teams: list[dict[str, Any]]) -> MatchDecision:
    normalized = normalize_team_code(raw_team)
    if not normalized:
        return MatchDecision(canonical_value="", confidence=0.0, method="unresolved", evidence={"raw": raw_team})

    by_code = {str(row.get("canonical_team_id") or ""): row for row in canonical_teams}
    if normalized in by_code:
        return MatchDecision(canonical_value=normalized, confidence=1.0, method="alias", evidence={"raw": raw_team})

    best_score = 0.0
    best_code = ""
    for row in canonical_teams:
        code = str(row.get("canonical_team_id") or "")
        score = _ratio(normalized, normalize_team_code(code))
        if score > best_score:
            best_score = score
            best_code = code

    if best_score >= 0.9:
        return MatchDecision(canonical_value=best_code, confidence=best_score, method="fuzzy", evidence={"raw": raw_team})
    return MatchDecision(canonical_value="", confidence=best_score, method="unresolved", evidence={"raw": raw_team})


def match_player(
    raw_player_name: str,
    canonical_players: list[dict[str, Any]],
    canonical_team_id: str,
    canonical_position_code: str,
) -> tuple[MatchDecision, list[dict[str, Any]]]:
    normalized_name = normalize_player_name(raw_player_name)
    if not normalized_name:
        return (
            MatchDecision(canonical_value="", confidence=0.0, method="unresolved", evidence={"raw": raw_player_name}),
            [],
        )

    exact_candidates: list[dict[str, Any]] = []
    fuzzy_candidates: list[dict[str, Any]] = []

    for player in canonical_players:
        canonical_id = str(player.get("canonical_player_id") or "")
        display_name = str(player.get("display_name") or "")
        aliases = player.get("aliases") or []
        alias_set = {normalize_player_name(str(display_name))} | {
            normalize_player_name(str(alias)) for alias in aliases
        }

        team_bonus = 0.0
        if canonical_team_id and canonical_team_id == str(player.get("current_team") or ""):
            team_bonus = 0.02

        position_bonus = 0.0
        if canonical_position_code and canonical_position_code == str(player.get("primary_position") or ""):
            position_bonus = 0.02

        if normalized_name in alias_set:
            exact_candidates.append(
                {
                    "canonical_player_id": canonical_id,
                    "display_name": display_name,
                    "score": min(1.0, 0.96 + team_bonus + position_bonus),
                    "method": "exact",
                }
            )
            continue

        score_candidates = [_ratio(normalized_name, normalize_player_name(display_name))] + [
            _ratio(normalized_name, normalize_player_name(str(a))) for a in aliases
        ]
        score = max(score_candidates) if score_candidates else 0.0
        if score > 0:
            fuzzy_candidates.append(
                {
                    "canonical_player_id": canonical_id,
                    "display_name": display_name,
                    "score": min(1.0, score + team_bonus + position_bonus),
                    "method": "fuzzy",
                }
            )

    ranked = sorted(exact_candidates + fuzzy_candidates, key=lambda r: r["score"], reverse=True)
    if not ranked:
        return (
            MatchDecision(canonical_value="", confidence=0.0, method="unresolved", evidence={"raw": raw_player_name}),
            [],
        )

    best = ranked[0]
    decision = MatchDecision(
        canonical_value=str(best["canonical_player_id"]),
        confidence=float(best["score"]),
        method=str(best["method"]),
        evidence={"raw": raw_player_name, "best_display_name": best["display_name"]},
    )
    return decision, ranked[:5]
