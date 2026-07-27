from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from nfl.yahoo_fantasy import build_oauth_session
from nfl.yahoo_fantasy.api import YahooApiClient
from nfl.storage_uc import UCTableConfig, persist_to_uc_tables


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pull Yahoo player pool for a season range.")
    parser.add_argument("--start-season", type=int, default=2021)
    parser.add_argument("--end-season", type=int, default=2023)
    parser.add_argument("--sport", default="nfl", choices=["nfl", "nba"])
    parser.add_argument("--player-page-size", type=int, default=10)
    parser.add_argument(
        "--request-interval-seconds", type=float, default=0.4,
        help="Delay between Yahoo API requests.",
    )
    parser.add_argument(
        "--max-request-retries", type=int, default=5,
    )
    parser.add_argument(
        "--backoff-base-seconds", type=float, default=1.2,
    )
    parser.add_argument(
        "--use-cache", action="store_true",
        help="Use cached API responses (default: fresh requests).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Skip writing to Iceberg; just print what would be written.",
    )
    return parser.parse_args()


def _load_credentials(root: Path) -> tuple[str, str, str]:
    credentials_path = root / ".secrets" / "credentials.json"

    creds: dict[str, str] = {}
    if credentials_path.exists():
        raw = json.loads(credentials_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            creds = raw

    client_id = os.environ.get("YAHOO_CLIENT_ID", creds.get("client_id", "")).strip()
    client_secret = os.environ.get("YAHOO_CLIENT_SECRET", creds.get("client_secret", "")).strip()
    redirect_uri = os.environ.get("YAHOO_REDIRECT_URI", creds.get("redirect_uri", "http://localhost:8000")).strip()

    if not client_id or not client_secret:
        raise RuntimeError(
            "Missing Yahoo OAuth credentials. Set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET "
            "in environment or .secrets/credentials.json."
        )
    return client_id, client_secret, redirect_uri


def main() -> None:
    os.chdir(ROOT)
    args = _parse_args()

    client_id, client_secret, redirect_uri = _load_credentials(ROOT)
    token_path = ROOT / ".secrets" / "yahoo_token.json"

    oauth = build_oauth_session(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        token_path=token_path,
        auth_code=None,
        open_browser=False,
    )

    client = YahooApiClient(
        oauth_session=oauth,
        cache_dir=ROOT / ".cache",
        use_cache=args.use_cache,
        validate_contracts=True,
        request_interval_seconds=args.request_interval_seconds,
        max_request_retries=args.max_request_retries,
        backoff_base_seconds=args.backoff_base_seconds,
        player_page_size=args.player_page_size,
    )

    print(f"Fetching {args.sport} players for seasons {args.start_season}–{args.end_season}...")
    rows = client.get_players_for_season_range(
        start_season=args.start_season,
        end_season=args.end_season,
        sport=args.sport,
    )
    print(f"Fetched {len(rows)} players across {args.start_season}–{args.end_season}")

    if not rows:
        print("No rows returned; nothing to write.")
        return

    df = pl.from_dicts(rows)
    game_ids = df["game_id"].unique().sort().to_list() if "game_id" in df.columns else []
    print(f"game_ids in result: {game_ids}")
    print(df.head(3))

    uc_config = UCTableConfig(
        catalog="nfl",
        schema="yh",
        write_mode="append",
    )

    results = persist_to_uc_tables(
        frames={"player": df},
        config=uc_config,
        dry_run=args.dry_run,
    )

    for r in results:
        status = "DRY RUN" if args.dry_run else "WRITTEN"
        print(f"  [{status}] {r.target}: {r.written_rows} rows ({r.mode})")

