"""Yahoo API adapters and normalization entrypoints."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from requests_oauthlib import OAuth2Session

from nfl.yahoo_fantasy.validation import validate

API_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"
LEAGUE_KEY_RE = re.compile(r"^\d+\.l\.\d+$")


def iter_dicts(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from iter_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_dicts(item)


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def pick_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        for item in value:
            scalar = pick_scalar(item)
            if scalar not in (None, ""):
                return scalar
        return ""
    if isinstance(value, dict):
        if "value" in value:
            return pick_scalar(value.get("value"))
        if "points" in value:
            return pick_scalar(value.get("points"))
        for key in sorted(value.keys(), key=lambda k: str(k)):
            scalar = pick_scalar(value.get(key))
            if scalar not in (None, ""):
                return scalar
    return ""


class YahooApiClient:
    def __init__(
        self,
        oauth_session: OAuth2Session,
        timeout_seconds: int = 30,
        cache_dir: Path | str = ".cache",
        use_cache: bool = True,
        validate_contracts: bool = True,
    ) -> None:
        self.oauth_session = oauth_session
        self.timeout_seconds = timeout_seconds
        self.cache_dir = Path(cache_dir)
        self.use_cache = use_cache
        self.validate_contracts = validate_contracts

    def _cache_file(self, path: str) -> Path:
        return self.cache_dir / f"{hashlib.md5(path.encode('utf-8')).hexdigest()}.json"

    def get(self, path: str, timeout_seconds: int | None = None) -> dict[str, Any]:
        timeout = timeout_seconds if timeout_seconds is not None else self.timeout_seconds
        cache_file = self._cache_file(path)
        if self.use_cache and cache_file.exists():
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass

        url = f"{API_BASE}{path}"
        resp = self.oauth_session.get(url, params={"format": "json"}, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        if self.use_cache:
            try:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(payload), encoding="utf-8")
            except OSError:
                pass
        return payload

    def discover_league_keys(self, sport: str = "all") -> list[str]:
        sport_value = (sport or "").strip().lower()
        if sport_value in {"", "all", "*"}:
            endpoints = ["/users;use_login=1/games/leagues"]
        else:
            endpoints = [
                f"/users;use_login=1/games;game_codes={sport_value}/leagues",
                f"/users;use_login=1/games;game_keys={sport_value}/leagues",
                "/users;use_login=1/games/leagues",
            ]
        keys: set[str] = set()
        for endpoint in endpoints:
            payload = self.get(endpoint)
            for item in iter_dicts(payload):
                league_key = item.get("league_key")
                if isinstance(league_key, str) and LEAGUE_KEY_RE.match(league_key):
                    keys.add(league_key)
        return sorted(keys)

    def get_league_metadata(self, league_key: str) -> dict[str, Any]:
        payload = self.get(f"/league/{league_key}/settings")
        season = 0
        league_name = ""
        game_code = ""
        scoring_type = ""
        league_type = ""
        num_teams: int | None = None
        start_week: int | None = None
        end_week: int | None = None
        current_week: int | None = None

        for item in iter_dicts(payload):
            if not season and item.get("season") is not None:
                season = to_int(item.get("season"), 0)
            if not league_name and isinstance(item.get("name"), str):
                league_name = item["name"]
            if not game_code and isinstance(item.get("game_code"), str):
                game_code = item["game_code"]
            if not scoring_type and isinstance(item.get("scoring_type"), str):
                scoring_type = item["scoring_type"]
            if not league_type and isinstance(item.get("league_type"), str):
                league_type = item["league_type"]
            if num_teams is None and item.get("num_teams") is not None:
                num_teams = to_int(item.get("num_teams"))
            if start_week is None and item.get("start_week") is not None:
                start_week = to_int(item.get("start_week"), 0)
            if end_week is None and item.get("end_week") is not None:
                end_week = to_int(item.get("end_week"), 0)
            if current_week is None and item.get("current_week") is not None:
                current_week = to_int(item.get("current_week"), 0)

        record = {
            "league_key": league_key,
            "league_id": league_key.split(".l.")[1] if ".l." in league_key else "",
            "game_id": to_int(league_key.split(".")[0]),
            "game_code": game_code.lower() if game_code else "",
            "season": season,
            "league_name": league_name,
            "scoring_type": scoring_type,
            "league_type": league_type,
            "num_teams": num_teams,
            "start_week": start_week,
            "end_week": end_week,
            "current_week": current_week,
        }
        if self.validate_contracts:
            validate([record], entity="league")
        return record

    def get_players(self, league_key: str) -> list[dict[str, Any]]:
        league_meta = self.get_league_metadata(league_key)
        game_id = league_meta["game_id"]

        rows_by_key: dict[str, dict[str, Any]] = {}
        start = 0
        count = 25
        max_pages = 200

        for _ in range(max_pages):
            payload = self.get(f"/league/{league_key}/players;start={start};count={count}")
            page_records = self._extract_players_from_payload(payload, game_id)
            if not page_records:
                break

            for record in page_records:
                rows_by_key[record["player_key"]] = record

            if len(page_records) < count:
                break
            start += count

        rows = sorted(rows_by_key.values(), key=lambda r: r["player_key"])
        if self.validate_contracts and rows:
            validate(rows, entity="player")
        return rows

    def get_teams(self, league_key: str) -> list[dict[str, Any]]:
        payload = self.get(f"/league/{league_key}/teams")
        league = payload.get("fantasy_content", {}).get("league", [])
        if len(league) < 2 or not isinstance(league[1], dict):
            return []
        teams_dict = league[1].get("teams", {})
        if not isinstance(teams_dict, dict):
            return []

        teams: list[dict[str, Any]] = []
        for team_entry in teams_dict.values():
            if not isinstance(team_entry, dict):
                continue
            team_array = team_entry.get("team", [])
            metadata = team_array[0] if isinstance(team_array, list) and team_array and isinstance(team_array[0], list) else []
            team_key = ""
            team_name = ""
            owner_name = ""
            draft_position: int | None = None
            for elem in metadata:
                if not isinstance(elem, dict):
                    continue
                if not team_key and isinstance(elem.get("team_key"), str):
                    team_key = elem["team_key"]
                if not team_name and isinstance(elem.get("name"), str):
                    team_name = elem["name"]
                if draft_position is None and elem.get("draft_position") is not None:
                    draft_position = to_int(elem.get("draft_position"))
                if "managers" in elem:
                    managers = elem.get("managers", [])
                    if isinstance(managers, list) and managers:
                        manager = managers[0].get("manager", {}) if isinstance(managers[0], dict) else {}
                        if isinstance(manager, dict):
                            owner_name = str(pick_scalar(manager.get("nickname")) or "")
            if not team_key:
                continue
            teams.append(
                {
                    "team_key": team_key,
                    "league_key": league_key,
                    "team_id": to_int(team_key.split(".t.")[1]) if ".t." in team_key else 0,
                    "team_name": team_name,
                    "owner_name": owner_name,
                    "draft_position": draft_position,
                }
            )

        if self.validate_contracts and teams:
            validate(teams, entity="team")
        return teams

    def get_draft_picks(self, league_key: str, season: int | None = None) -> list[dict[str, Any]]:
        payload = self.get(f"/league/{league_key}/draftresults;out=players")
        season_value = season if season is not None else self.get_league_metadata(league_key)["season"]
        picks: list[dict[str, Any]] = []
        for item in iter_dicts(payload):
            if "round" not in item or "pick" not in item:
                continue
            team_key = item.get("team_key")
            player_key = item.get("player_key")
            if not team_key or not player_key:
                continue
            cost_raw = item.get("cost")
            cost = to_int(cost_raw) if cost_raw not in (None, "") else None
            picks.append(
                {
                    "league_key": league_key,
                    "season": season_value,
                    "team_key": str(team_key),
                    "player_key": str(player_key),
                    "pick_number": to_int(item.get("pick")),
                    "round_number": to_int(item.get("round")),
                    "cost": cost,
                }
            )
        picks.sort(key=lambda r: (r["round_number"], r["pick_number"]))
        if self.validate_contracts and picks:
            validate(picks, entity="draft_pick")
        return picks

    def get_stat_categories(self, league_key: str, game_id: int | None = None) -> list[dict[str, Any]]:
        resolved_game_id = game_id if game_id is not None else self.get_league_metadata(league_key)["game_id"]
        payload = self.get(f"/game/{resolved_game_id}/stat_categories")

        rows_by_id: dict[str, dict[str, Any]] = {}
        for item in iter_dicts(payload):
            if not isinstance(item, dict) or "stat" not in item:
                continue

            stat_block = item.get("stat")
            if not isinstance(stat_block, list):
                continue

            stat_id = ""
            display_name = ""
            name = ""
            for part in stat_block:
                if not isinstance(part, dict):
                    continue
                if not stat_id and part.get("stat_id") not in (None, ""):
                    stat_id = str(pick_scalar(part.get("stat_id")) or "").strip()
                if not display_name:
                    display_name = str(
                        pick_scalar(part.get("display_name"))
                        or pick_scalar(part.get("abbr"))
                        or ""
                    ).strip()
                if not name:
                    name = str(pick_scalar(part.get("name")) or "").strip()

            if not stat_id:
                continue
            if not display_name:
                display_name = name
            if not name:
                name = display_name
            if not display_name or not name:
                continue

            rows_by_id[stat_id] = {
                "game_id": resolved_game_id,
                "stat_id": stat_id,
                "display_name": display_name,
                "name": name,
            }

        for item in iter_dicts(payload):
            stat_id_raw = item.get("stat_id")
            if stat_id_raw in (None, ""):
                continue
            stat_id = str(pick_scalar(stat_id_raw) or "").strip()
            if not stat_id:
                continue

            display_name = str(
                pick_scalar(item.get("display_name"))
                or pick_scalar(item.get("abbr"))
                or pick_scalar(item.get("name"))
                or ""
            ).strip()
            name = str(pick_scalar(item.get("name")) or display_name).strip()
            if not display_name:
                display_name = name
            if not name:
                name = display_name
            if not display_name or not name:
                continue

            rows_by_id[stat_id] = {
                "game_id": resolved_game_id,
                "stat_id": stat_id,
                "display_name": display_name,
                "name": name,
            }

        rows = sorted(rows_by_id.values(), key=lambda r: r["stat_id"])
        if self.validate_contracts and rows:
            validate(rows, entity="stat_category")
        return rows

    def get_scoring_rules(self, league_key: str, season: int | None = None) -> list[dict[str, Any]]:
        season_value = season if season is not None else self.get_league_metadata(league_key)["season"]
        payload = self.get(f"/league/{league_key}/settings")

        rows_by_id: dict[str, dict[str, Any]] = {}
        for item in iter_dicts(payload):
            if not isinstance(item, dict) or "scoring_rule" not in item:
                continue

            rule_block = item.get("scoring_rule")
            if not isinstance(rule_block, list):
                continue

            stat_id = ""
            points_per_unit = 0.0
            bonus_target: float | None = None
            bonus_points: float | None = None
            for part in rule_block:
                if not isinstance(part, dict):
                    continue
                if not stat_id and part.get("stat_id") not in (None, ""):
                    stat_id = str(pick_scalar(part.get("stat_id")) or "").strip()

                ppu_raw = (
                    pick_scalar(part.get("value"))
                    or pick_scalar(part.get("points"))
                    or pick_scalar(part.get("modifier"))
                    or pick_scalar(part.get("points_per_unit"))
                )
                if points_per_unit == 0.0 and ppu_raw not in (None, ""):
                    points_per_unit = to_float(ppu_raw, 0.0)

                target_raw = pick_scalar(part.get("bonus_target")) or pick_scalar(part.get("target"))
                if bonus_target is None and target_raw not in (None, ""):
                    bonus_target = to_float(target_raw, 0.0)

                bonus_raw = pick_scalar(part.get("bonus_points")) or pick_scalar(part.get("bonus"))
                if bonus_points is None and bonus_raw not in (None, ""):
                    bonus_points = to_float(bonus_raw, 0.0)

            if not stat_id:
                continue

            rows_by_id[stat_id] = {
                "league_key": league_key,
                "season": season_value,
                "stat_id": stat_id,
                "points_per_unit": points_per_unit,
                "bonus_target": bonus_target,
                "bonus_points": bonus_points,
            }

        for item in iter_dicts(payload):
            stat_id_raw = item.get("stat_id")
            if stat_id_raw in (None, ""):
                continue
            stat_id = str(pick_scalar(stat_id_raw) or "").strip()
            if not stat_id:
                continue

            ppu_raw = (
                pick_scalar(item.get("value"))
                or pick_scalar(item.get("points"))
                or pick_scalar(item.get("modifier"))
                or pick_scalar(item.get("points_per_unit"))
            )
            points_per_unit = to_float(ppu_raw, 0.0)

            bonus_target_raw = pick_scalar(item.get("bonus_target")) or pick_scalar(item.get("target"))
            bonus_points_raw = pick_scalar(item.get("bonus_points")) or pick_scalar(item.get("bonus"))

            existing = rows_by_id.get(stat_id)
            if existing is not None:
                if existing["points_per_unit"] == 0.0 and points_per_unit != 0.0:
                    existing["points_per_unit"] = points_per_unit
                if existing["bonus_target"] is None and bonus_target_raw not in (None, ""):
                    existing["bonus_target"] = to_float(bonus_target_raw, 0.0)
                if existing["bonus_points"] is None and bonus_points_raw not in (None, ""):
                    existing["bonus_points"] = to_float(bonus_points_raw, 0.0)
                continue

            rows_by_id[stat_id] = {
                "league_key": league_key,
                "season": season_value,
                "stat_id": stat_id,
                "points_per_unit": points_per_unit,
                "bonus_target": to_float(bonus_target_raw, 0.0) if bonus_target_raw not in (None, "") else None,
                "bonus_points": to_float(bonus_points_raw, 0.0) if bonus_points_raw not in (None, "") else None,
            }

        rows = sorted(rows_by_id.values(), key=lambda r: r["stat_id"])
        if self.validate_contracts and rows:
            validate(rows, entity="scoring_rule")
        return rows

    def get_transactions(self, league_key: str, season: int | None = None) -> list[dict[str, Any]]:
        payload = self.get(f"/league/{league_key}/transactions")
        season_value = season if season is not None else self.get_league_metadata(league_key)["season"]
        rows: list[dict[str, Any]] = []
        leagues = payload.get("fantasy_content", {}).get("league", [])
        if len(leagues) < 2 or not isinstance(leagues[1], dict):
            return rows
        txs = leagues[1].get("transactions", {})
        if not isinstance(txs, dict):
            return rows

        for tx_entry in txs.values():
            if not isinstance(tx_entry, dict) or "transaction" not in tx_entry:
                continue
            tx_array = tx_entry["transaction"]
            if not isinstance(tx_array, list) or not tx_array:
                continue
            raw0 = tx_array[0]
            tx_meta: dict[str, Any] | None = raw0 if isinstance(raw0, dict) else None
            if tx_meta is None and isinstance(raw0, list):
                tx_meta = next((x for x in raw0 if isinstance(x, dict)), None)
            if not tx_meta:
                continue
            tx_id = str(tx_meta.get("transaction_id") or "")
            tx_type = str(tx_meta.get("type") or "")
            status = str(tx_meta.get("status") or "")
            if not tx_id or not tx_type:
                continue

            source_team_key: str | None = None
            destination_team_key: str | None = None
            player_keys: list[str] = []
            for elem in tx_array[1:]:
                if not isinstance(elem, dict):
                    continue
                if "transaction_data" in elem and isinstance(elem["transaction_data"], list):
                    for d in elem["transaction_data"]:
                        if not isinstance(d, dict):
                            continue
                        if not source_team_key and d.get("source_team_key"):
                            source_team_key = str(d.get("source_team_key"))
                        if not destination_team_key and d.get("destination_team_key"):
                            destination_team_key = str(d.get("destination_team_key"))
                        if d.get("player_key"):
                            player_keys.append(str(d.get("player_key")))
                if "players" in elem and isinstance(elem["players"], dict):
                    for pe in elem["players"].values():
                        if not isinstance(pe, dict) or "player" not in pe:
                            continue
                        player_array = pe["player"]
                        if not isinstance(player_array, list) or not player_array:
                            continue
                        meta = player_array[0] if isinstance(player_array[0], list) else []
                        for m in meta:
                            if isinstance(m, dict) and m.get("player_key"):
                                player_keys.append(str(m.get("player_key")))

            tx_key = f"{league_key}.tr.{tx_id}"
            for player_key in sorted(set(player_keys)):
                rows.append(
                    {
                        "transaction_key": tx_key,
                        "league_key": league_key,
                        "season": season_value,
                        "transaction_type": tx_type,
                        "status": status,
                        "player_key": player_key,
                        "source_team_key": source_team_key,
                        "destination_team_key": destination_team_key,
                    }
                )
        if self.validate_contracts and rows:
            validate(rows, entity="transaction")
        return rows

    def get_standings(self, league_key: str, sport: str | None = None) -> list[dict[str, Any]]:
        league_meta = self.get_league_metadata(league_key)
        payload = self.get(f"/league/{league_key}/standings")
        teams = self._extract_standing_teams(payload)
        if not teams:
            teams = self._extract_standing_teams(self.get(f"/league/{league_key}/teams;out=standings"))

        game_code = (sport or league_meta.get("game_code") or "").lower()
        season = league_meta["season"]
        scoring_type = league_meta.get("scoring_type", "")

        if game_code == "nba":
            rows = self._normalize_nba_standings(league_key, season, scoring_type, teams)
            if self.validate_contracts and rows:
                validate(rows, entity="standings", sport="nba")
            return rows

        rows = self._normalize_nfl_standings(league_key, season, teams)
        if self.validate_contracts and rows:
            validate(rows, entity="standings", sport="nfl")
        return rows

    def get_matchups(self, league_key: str, season: int, weeks: list[int]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for week in weeks:
            payload = self.get(f"/league/{league_key}/scoreboard;week={week}")
            for left, right, matchup_week, is_playoff, is_consolation in self._extract_weekly_matchup_pairs(payload):
                rows.append(
                    {
                        "league_key": league_key,
                        "season": season,
                        "week": matchup_week if matchup_week > 0 else week,
                        "team_key": left["team_key"],
                        "opponent_team_key": right["team_key"],
                        "points": left["points"],
                        "opponent_points": right["points"],
                        "is_playoff": is_playoff,
                        "is_consolation": is_consolation,
                    }
                )
                rows.append(
                    {
                        "league_key": league_key,
                        "season": season,
                        "week": matchup_week if matchup_week > 0 else week,
                        "team_key": right["team_key"],
                        "opponent_team_key": left["team_key"],
                        "points": right["points"],
                        "opponent_points": left["points"],
                        "is_playoff": is_playoff,
                        "is_consolation": is_consolation,
                    }
                )

        rows.sort(key=lambda r: (r["week"], r["team_key"]))
        if self.validate_contracts and rows:
            validate(rows, entity="matchups", sport="nfl")
        return rows

    def get_roster_entries(
        self,
        league_key: str,
        season: int,
        weeks: list[int],
        team_keys: list[str],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for week in weeks:
            for team_key in team_keys:
                try:
                    payload = self.get(f"/team/{team_key}/roster;week={week};out=players,stats")
                except Exception:
                    payload = self.get(f"/team/{team_key}/roster;week={week};out=players")
                rows.extend(self._extract_team_roster_entries(payload, league_key, season, week, team_key))

        rows.sort(key=lambda r: (r["week"], r["team_key"], r["player_key"]))
        if self.validate_contracts and rows:
            validate(rows, entity="roster_entries", sport="nfl")
        return rows

    def get_player_stats_weekly(
        self,
        league_key: str,
        season: int,
        roster_entries: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, int, str]] = set()

        for entry in roster_entries:
            week = to_int(entry.get("week"), 0)
            player_key = str(entry.get("player_key") or "")
            if week <= 0 or not player_key:
                continue

            pk = (league_key, week, player_key)
            if pk in seen:
                continue
            seen.add(pk)

            points_raw = entry.get("points")
            points = to_float(points_raw, 0.0) if points_raw is not None else 0.0
            bye_week_raw = entry.get("bye_week")
            rows.append(
                {
                    "league_key": league_key,
                    "season": season,
                    "week": week,
                    "player_key": player_key,
                    "fantasy_points": points,
                    "status": str(entry.get("status") or "") or None,
                    "bye_week": to_int(bye_week_raw, 0) if bye_week_raw not in (None, "") else None,
                    "stats": list(entry.get("stats") or []),
                }
            )

        rows.sort(key=lambda r: (r["week"], r["player_key"]))
        if self.validate_contracts and rows:
            validate(rows, entity="player_stats_weekly", sport="nfl")
        return rows

    def _extract_standing_teams(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        leagues = payload.get("fantasy_content", {}).get("league", [])
        if len(leagues) < 2 or not isinstance(leagues[1], dict):
            return []
        container = leagues[1]
        teams_dict: Any = None
        if "standings" in container and isinstance(container["standings"], list) and container["standings"]:
            s0 = container["standings"][0]
            if isinstance(s0, dict):
                teams_dict = s0.get("teams", {})
        if not teams_dict:
            teams_dict = container.get("teams", {})
        if not isinstance(teams_dict, dict):
            return []

        out: list[dict[str, Any]] = []
        for team_entry in teams_dict.values():
            if not isinstance(team_entry, dict):
                continue
            team_array = team_entry.get("team", [])
            if not isinstance(team_array, list) or not team_array:
                continue
            meta = team_array[0] if isinstance(team_array[0], list) else []
            team_key = ""
            team_name = ""
            owner_name = ""
            for elem in meta:
                if not isinstance(elem, dict):
                    continue
                if not team_key and isinstance(elem.get("team_key"), str):
                    team_key = elem["team_key"]
                if not team_name and isinstance(elem.get("name"), str):
                    team_name = elem["name"]
                if "managers" in elem:
                    managers = elem.get("managers", [])
                    if isinstance(managers, list) and managers:
                        manager = managers[0].get("manager", {}) if isinstance(managers[0], dict) else {}
                        if isinstance(manager, dict):
                            owner_name = str(pick_scalar(manager.get("nickname")) or "")
            ts = {}
            tp = {}
            for elem in team_array[1:]:
                if not isinstance(elem, dict):
                    continue
                if "team_standings" in elem and isinstance(elem["team_standings"], dict):
                    ts = elem["team_standings"]
                if "team_points" in elem and isinstance(elem["team_points"], dict):
                    tp = elem["team_points"]
            if team_key:
                out.append({"team_key": team_key, "team_name": team_name, "owner_name": owner_name, "team_standings": ts, "team_points": tp})
        return out

    def _normalize_nfl_standings(self, league_key: str, season: int, teams: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for team in teams:
            ts = team.get("team_standings", {})
            outcome = ts.get("outcome_totals", {}) if isinstance(ts, dict) else {}
            rows.append(
                {
                    "league_key": league_key,
                    "season": season,
                    "team_key": team["team_key"],
                    "rank": to_int(pick_scalar(ts.get("rank")), 0),
                    "wins": to_int(pick_scalar(outcome.get("wins")), 0),
                    "losses": to_int(pick_scalar(outcome.get("losses")), 0),
                    "ties": to_int(pick_scalar(outcome.get("ties")), 0),
                    "points_for": to_float(pick_scalar(ts.get("points_for")), 0.0),
                    "points_against": to_float(pick_scalar(ts.get("points_against")), 0.0),
                }
            )
        return rows

    def _normalize_nba_standings(self, league_key: str, season: int, scoring_type: str, teams: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for team in teams:
            ts = team.get("team_standings", {})
            tp = team.get("team_points", {})
            rows.append(
                {
                    "league_key": league_key,
                    "season": season,
                    "team_key": team["team_key"],
                    "rank": to_int(pick_scalar(ts.get("rank")), 0),
                    "scoring_type": scoring_type,
                    "points_for": to_float(pick_scalar(tp.get("total")), 0.0),
                }
            )
        if rows and all(r["rank"] == 0 for r in rows):
            ranked = sorted(rows, key=lambda r: r["points_for"], reverse=True)
            for idx, row in enumerate(ranked, start=1):
                row["rank"] = idx
            return ranked
        return rows

    def _extract_players_from_payload(self, payload: dict[str, Any], game_id: int) -> list[dict[str, Any]]:
        rows_by_key: dict[str, dict[str, Any]] = {}

        league = payload.get("fantasy_content", {}).get("league", [])
        if len(league) >= 2 and isinstance(league[1], dict):
            players_dict = league[1].get("players", {})
            if isinstance(players_dict, dict):
                for player_entry in players_dict.values():
                    if not isinstance(player_entry, dict):
                        continue
                    player_array = player_entry.get("player", [])
                    if not isinstance(player_array, list) or not player_array:
                        continue
                    metadata = player_array[0] if isinstance(player_array[0], list) else []
                    if not isinstance(metadata, list):
                        continue

                    player_key = ""
                    player_id: int | None = None
                    full_name = ""
                    display_position = ""
                    editorial_team_abbr: str | None = None

                    for m in metadata:
                        if not isinstance(m, dict):
                            continue
                        if not player_key and m.get("player_key"):
                            player_key = str(m.get("player_key"))
                        if player_id is None and m.get("player_id") is not None:
                            player_id = to_int(m.get("player_id"), 0)
                        if not full_name and isinstance(m.get("name"), dict):
                            full_name = str(m["name"].get("full") or "").strip()
                        if not display_position and m.get("display_position") is not None:
                            display_position = str(m.get("display_position") or "").strip()
                        if editorial_team_abbr is None and m.get("editorial_team_abbr"):
                            editorial_team_abbr = str(m.get("editorial_team_abbr"))

                    if player_key and player_id is not None and full_name and display_position:
                        rows_by_key[player_key] = {
                            "player_key": player_key,
                            "player_id": player_id,
                            "game_id": game_id,
                            "full_name": full_name,
                            "display_position": display_position,
                            "editorial_team_abbr": editorial_team_abbr,
                        }

        for item in iter_dicts(payload):
            player_key = item.get("player_key")
            player_id = item.get("player_id")
            if not player_key or player_id is None:
                continue

            raw_name = item.get("name")
            if isinstance(raw_name, dict):
                full_name = str(raw_name.get("full") or "").strip()
            else:
                full_name = str(raw_name or "").strip()
            display_position = str(item.get("display_position") or "").strip()
            if not full_name or not display_position:
                continue

            rows_by_key[str(player_key)] = {
                "player_key": str(player_key),
                "player_id": to_int(player_id),
                "game_id": game_id,
                "full_name": full_name,
                "display_position": display_position,
                "editorial_team_abbr": str(item.get("editorial_team_abbr") or "") or None,
            }
        return list(rows_by_key.values())

    def _extract_weekly_matchup_pairs(
        self,
        payload: dict[str, Any],
    ) -> list[tuple[dict[str, Any], dict[str, Any], int, bool, bool]]:
        out: list[tuple[dict[str, Any], dict[str, Any], int, bool, bool]] = []
        for item in iter_dicts(payload):
            matchup_node = item.get("matchup") if isinstance(item, dict) else None
            if not isinstance(matchup_node, (list, dict)):
                continue

            matchup_array = matchup_node if isinstance(matchup_node, list) else [matchup_node]

            matchup_week = 0
            is_playoff = False
            is_consolation = False
            teams_dict: dict[str, Any] | None = None
            for elem in matchup_array:
                if not isinstance(elem, dict):
                    continue
                if matchup_week == 0 and elem.get("week") is not None:
                    matchup_week = to_int(elem.get("week"), 0)
                if elem.get("is_playoffs") is not None:
                    is_playoff = str(elem.get("is_playoffs")).strip() == "1"
                if elem.get("is_consolation") is not None:
                    is_consolation = str(elem.get("is_consolation")).strip() == "1"
                if "teams" in elem and isinstance(elem["teams"], dict):
                    teams_dict = elem["teams"]
                if teams_dict is None:
                    numeric_children = [v for k, v in elem.items() if str(k).isdigit() and isinstance(v, dict)]
                    for child in numeric_children:
                        if "teams" in child and isinstance(child["teams"], dict):
                            teams_dict = child["teams"]
                            break

            if not teams_dict or not isinstance(teams_dict, dict):
                continue

            parsed_teams: list[dict[str, Any]] = []
            for team_entry in teams_dict.values():
                team = self._extract_scoreboard_team(team_entry)
                if team is not None:
                    parsed_teams.append(team)

            if len(parsed_teams) != 2:
                continue
            out.append((parsed_teams[0], parsed_teams[1], matchup_week, is_playoff, is_consolation))

        return out

    def _extract_scoreboard_team(self, team_entry: Any) -> dict[str, Any] | None:
        if not isinstance(team_entry, dict):
            return None
        team_array = team_entry.get("team", [])
        if not isinstance(team_array, list) or not team_array:
            return None

        team_key = ""
        points = 0.0
        for elem in team_array:
            if isinstance(elem, list):
                for m in elem:
                    if isinstance(m, dict) and not team_key and m.get("team_key"):
                        team_key = str(m.get("team_key"))
            elif isinstance(elem, dict):
                if "team_points" in elem and isinstance(elem["team_points"], dict):
                    points = to_float(pick_scalar(elem["team_points"].get("total")), 0.0)
                if not team_key and elem.get("team_key"):
                    team_key = str(elem.get("team_key"))

        if not team_key:
            return None
        return {"team_key": team_key, "points": points}

    def _extract_team_roster_entries(
        self,
        payload: dict[str, Any],
        league_key: str,
        season: int,
        week: int,
        team_key: str,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for item in iter_dicts(payload):
            player_array = item.get("player") if isinstance(item, dict) else None
            if not isinstance(player_array, list) or not player_array:
                continue

            player_key = ""
            selected_position = ""
            points: float | None = None
            status: str | None = None
            bye_week: int | None = None
            stats: list[dict[str, Any]] = []
            for elem in player_array:
                if isinstance(elem, list):
                    for m in elem:
                        if not isinstance(m, dict):
                            continue
                        if not player_key and m.get("player_key"):
                            player_key = str(m.get("player_key"))
                        if status is None and m.get("status") not in (None, ""):
                            status = str(m.get("status"))
                        if bye_week is None and m.get("bye_weeks") is not None:
                            bw = m.get("bye_weeks")
                            if isinstance(bw, dict):
                                bye_val = pick_scalar(bw.get("week"))
                                if bye_val not in (None, ""):
                                    bye_week = to_int(bye_val, 0)
                elif isinstance(elem, dict):
                    if "selected_position" in elem and isinstance(elem["selected_position"], dict):
                        selected_position = str(elem["selected_position"].get("position") or "")
                    if "selected_position" in elem and isinstance(elem["selected_position"], list):
                        for sp in elem["selected_position"]:
                            if isinstance(sp, dict) and sp.get("position"):
                                selected_position = str(sp.get("position") or "")
                    if "player_points" in elem and isinstance(elem["player_points"], dict):
                        points = to_float(pick_scalar(elem["player_points"].get("total")), 0.0)
                    if "player_points" in elem and isinstance(elem["player_points"], list):
                        for pp in elem["player_points"]:
                            if isinstance(pp, dict) and pp.get("total") not in (None, ""):
                                points = to_float(pp.get("total"), 0.0)
                    if "player_stats" in elem:
                        stats = self._extract_player_stat_lines(elem.get("player_stats"))

            if not player_key or not selected_position:
                continue

            bench_positions = {"BN", "IR", "IR+", "NA"}
            out.append(
                {
                    "league_key": league_key,
                    "season": season,
                    "week": week,
                    "team_key": team_key,
                    "player_key": player_key,
                    "selected_position": selected_position,
                    "is_starting": selected_position not in bench_positions,
                    "points": points,
                    "status": status,
                    "bye_week": bye_week,
                    "stats": stats,
                }
            )
        return out

    def _extract_player_stat_lines(self, player_stats: Any) -> list[dict[str, Any]]:
        lines: list[dict[str, Any]] = []
        for item in iter_dicts(player_stats):
            stat_id_raw = item.get("stat_id") if isinstance(item, dict) else None
            if stat_id_raw in (None, ""):
                continue

            value_raw = None
            if isinstance(item, dict):
                value_raw = pick_scalar(item.get("value"))
                if value_raw in (None, ""):
                    value_raw = pick_scalar(item.get("points"))

            stat_id = str(pick_scalar(stat_id_raw) or "").strip()
            if not stat_id or value_raw in (None, ""):
                continue

            lines.append(
                {
                    "stat_id": stat_id,
                    "value": to_float(value_raw, 0.0),
                }
            )

        dedup: dict[str, dict[str, Any]] = {row["stat_id"]: row for row in lines}
        return [dedup[key] for key in sorted(dedup.keys())]


def fetch_league_payload(oauth_session: OAuth2Session, league_key: str, timeout_seconds: int = 30) -> dict[str, Any]:
    client = YahooApiClient(oauth_session=oauth_session, timeout_seconds=timeout_seconds)
    return client.get(f"/league/{league_key}/settings")
