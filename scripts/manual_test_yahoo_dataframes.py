from __future__ import annotations

import argparse
import getpass
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
import webbrowser

import polars as pl
from requests_oauthlib import OAuth2Session
from requests.exceptions import HTTPError

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nfl.yahoo_fantasy import PipelineConfig, YahooApiClient, build_oauth_session, run_pipeline
from nfl.yahoo_fantasy.auth import AUTH_URL, SCOPES, extract_auth_code
from nfl.yahoo_fantasy.storage.iceberg import IcebergCatalogConfig, IcebergNamespaceConfig


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manual Yahoo data pull and DataFrame preview utility.",
    )
    parser.add_argument("--league-key", required=True, help="Yahoo league key, for example 461.l.717896")
    parser.add_argument("--sport", default="nfl", choices=["nfl", "nba"], help="Yahoo sport code")
    parser.add_argument("--head", type=int, default=5, help="Number of rows to preview per frame")
    parser.add_argument(
        "--entities",
        default="",
        help="Optional comma-separated frame names to preview. Example: yh_league,yhnfl_standings",
    )
    parser.add_argument(
        "--token-path",
        default=".secrets/yahoo_token.json",
        help="Path to cached Yahoo OAuth token JSON",
    )
    parser.add_argument(
        "--auth-code",
        default=os.getenv("YAHOO_AUTH_CODE", ""),
        help="Yahoo OAuth authorization code. Required only on first run without a cached token.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open Yahoo authorization URL in browser when token is not cached.",
    )
    parser.add_argument(
        "--disable-cache",
        action="store_true",
        help="Disable Yahoo API response caching for this run.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional dotenv file to load before reading environment variables.",
    )
    parser.add_argument("--client-id", default="", help="Yahoo OAuth client id override")
    parser.add_argument("--client-secret", default="", help="Yahoo OAuth client secret override")
    parser.add_argument("--redirect-uri", default="", help="Yahoo OAuth redirect URI override")
    parser.add_argument(
        "--access-token-json",
        default="",
        help="Yahoo OAuth token JSON override. If set, client-id/secret/redirect are optional.",
    )
    parser.add_argument(
        "--no-prompt-missing",
        action="store_true",
        help="Disable interactive prompts for missing OAuth values.",
    )
    parser.add_argument(
        "--auth-mode",
        default="auto",
        choices=["auto", "oauth", "token_json"],
        help="Authentication mode. auto prefers OAuth flow (cached token/refresh) then token_json.",
    )
    parser.add_argument(
        "--storage-target",
        default="none",
        choices=["none", "polars", "iceberg", "both"],
        help="Persistence target. Use polars to write local table files, iceberg for Iceberg writes, or both.",
    )
    parser.add_argument(
        "--polars-output-dir",
        default="./output/yahoo_polars",
        help="Output directory for local Polars table files.",
    )
    parser.add_argument(
        "--polars-file-format",
        default="parquet",
        choices=["parquet", "csv", "ndjson"],
        help="File format for local Polars persistence.",
    )
    parser.add_argument(
        "--iceberg-dry-run",
        action="store_true",
        help="Plan Iceberg writes without appending rows.",
    )
    parser.add_argument(
        "--iceberg-idempotency-store",
        default=".iceberg/write_log.json",
        help="Path for idempotency write log used by Iceberg persistence.",
    )
    parser.add_argument(
        "--iceberg-uri",
        default="sqlite:///iceberg_catalog.db",
        help="Iceberg SQL catalog URI.",
    )
    parser.add_argument(
        "--iceberg-warehouse",
        default="./warehouse",
        help="Iceberg warehouse directory.",
    )
    parser.add_argument(
        "--iceberg-nfl-namespace",
        default="yhnfl",
        help="Iceberg namespace for NFL entities.",
    )
    parser.add_argument(
        "--iceberg-nba-namespace",
        default="ynbna",
        help="Iceberg namespace for NBA entities.",
    )
    parser.add_argument(
        "--audit-iceberg",
        action="store_true",
        help="After Iceberg load, query each target table and print current row counts.",
    )
    return parser.parse_args()


def _load_env_fallback(env_path: Path) -> None:
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _resolve_required(
    value: str,
    env_name: str,
    cli_flag: str,
    prompt_label: str,
    prompt_missing: bool,
    secret: bool = False,
) -> str:
    resolved = (value or os.getenv(env_name, "")).strip()
    if resolved:
        return resolved

    if prompt_missing and sys.stdin.isatty():
        entered = getpass.getpass(f"{prompt_label}: ") if secret else input(f"{prompt_label}: ")
        entered = entered.strip()
        if entered:
            return entered

    raise ValueError(
        "Missing Yahoo OAuth setting. Provide via CLI or env variable: "
        f"--{cli_flag} or {env_name}"
    )


def _build_oauth_from_token_json(token_json: str) -> OAuth2Session:
    token_text = token_json.strip()

    # Accept either a JSON object or a JSON-encoded string that contains JSON.
    parsed: object
    try:
        parsed = json.loads(token_text)
    except json.JSONDecodeError as exc:
        # Some .env formats store escaped JSON without outer quotes.
        unescaped = token_text.replace('\\"', '"')
        try:
            parsed = json.loads(unescaped)
        except json.JSONDecodeError as inner_exc:
            raise ValueError(
                "Invalid Yahoo OAuth token JSON in --access-token-json or YAHOO_ACCESS_TOKEN_JSON"
            ) from inner_exc

    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Token JSON resolved to a string but could not be parsed as a JSON object"
            ) from exc

    token = parsed

    if not isinstance(token, dict) or "access_token" not in token:
        raise ValueError("Token JSON must be an object containing at least access_token")

    return OAuth2Session(token=token)


def _build_oauth_via_auth_flow(args: argparse.Namespace, prompt_missing: bool) -> OAuth2Session:
    client_id = _resolve_required(
        args.client_id,
        "YAHOO_CLIENT_ID",
        "client-id",
        "Enter Yahoo client ID",
        prompt_missing=prompt_missing,
    )
    client_secret = _resolve_required(
        args.client_secret,
        "YAHOO_CLIENT_SECRET",
        "client-secret",
        "Enter Yahoo client secret",
        prompt_missing=prompt_missing,
        secret=True,
    )
    redirect_uri = _resolve_required(
        args.redirect_uri,
        "YAHOO_REDIRECT_URI",
        "redirect-uri",
        "Enter Yahoo redirect URI",
        prompt_missing=prompt_missing,
    )

    auth_code = (args.auth_code or "").strip()
    token_path = Path(args.token_path)
    if not token_path.exists() and not auth_code and prompt_missing and sys.stdin.isatty():
        preflight_oauth = OAuth2Session(client_id=client_id, redirect_uri=redirect_uri, scope=SCOPES)
        authorization_url, _state = preflight_oauth.authorization_url(AUTH_URL)
        print("No cached Yahoo token found. Open this URL to authorize:")
        print(authorization_url)
        if args.open_browser:
            webbrowser.open(authorization_url)
        raw_code = input("Paste full redirect URL or code: ").strip()
        auth_code = extract_auth_code(raw_code)
        if not auth_code:
            raise ValueError("No authorization code provided. Re-run and paste the Yahoo redirect URL or code.")

    return build_oauth_session(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        token_path=token_path,
        auth_code=auth_code or None,
        open_browser=args.open_browser,
    )


def _select_frames(frames: dict[str, pl.DataFrame], entities_arg: str) -> dict[str, pl.DataFrame]:
    requested = [item.strip() for item in entities_arg.split(",") if item.strip()]
    if not requested:
        return frames
    return {name: frame for name, frame in frames.items() if name in set(requested)}


LEAGUE_KEY_RE = re.compile(r"^(\d+)\.l\.(\d+)$")


def _resolve_league_key(client: YahooApiClient, league_key: str, sport: str) -> str:
    discovered = client.discover_league_keys(sport=sport)
    if not discovered:
        return league_key
    if league_key in discovered:
        return league_key

    match = LEAGUE_KEY_RE.match(league_key)
    if not match:
        return league_key

    requested_game_id, requested_league_id = match.group(1), match.group(2)
    same_league_id = [key for key in discovered if key.endswith(f".l.{requested_league_id}")]

    details: list[str] = ["League key was not found in accessible leagues for this user."]
    if same_league_id:
        details.append(
            f"Candidates with same league id suffix ({requested_league_id}): {', '.join(sorted(same_league_id))}"
        )
    else:
        sample = ", ".join(discovered[:10])
        details.append(f"Discovered {len(discovered)} accessible league keys. Sample: {sample}")
    details.append(
        f"Requested key: {league_key} (game_id {requested_game_id}). Use the exact league_key shown in Yahoo."
    )
    raise ValueError(" ".join(details))


def _audit_iceberg_tables(
    catalog_config: IcebergCatalogConfig,
    table_identifiers: list[str],
) -> list[tuple[str, int | None, str | None]]:
    from pyiceberg.catalog import load_catalog

    catalog: Any = load_catalog(
        catalog_config.catalog_name,
        type=catalog_config.catalog_type,
        uri=catalog_config.uri,
        warehouse=catalog_config.warehouse,
    )

    rows: list[tuple[str, int | None, str | None]] = []
    for identifier in sorted(set(table_identifiers)):
        try:
            table = catalog.load_table(identifier)
            row_count = table.scan().to_arrow().num_rows
            rows.append((identifier, int(row_count), None))
        except Exception as exc:
            rows.append((identifier, None, str(exc)))
    return rows


def main() -> None:
    args = _parse_args()

    env_path = Path(args.env_file)
    if env_path.exists():
        if load_dotenv is not None:
            load_dotenv(env_path)
        else:
            _load_env_fallback(env_path)

    prompt_missing = not args.no_prompt_missing

    token_json = (args.access_token_json or os.getenv("YAHOO_ACCESS_TOKEN_JSON", "")).strip()
    has_oauth_settings = bool(
        (args.client_id or os.getenv("YAHOO_CLIENT_ID", "")).strip()
        and (args.client_secret or os.getenv("YAHOO_CLIENT_SECRET", "")).strip()
        and (args.redirect_uri or os.getenv("YAHOO_REDIRECT_URI", "")).strip()
    )

    used_token_json_auth = False
    if args.auth_mode == "oauth":
        oauth = _build_oauth_via_auth_flow(args, prompt_missing=prompt_missing)
    elif args.auth_mode == "token_json":
        if not token_json:
            raise ValueError("auth-mode=token_json requires --access-token-json or YAHOO_ACCESS_TOKEN_JSON")
        oauth = _build_oauth_from_token_json(token_json)
        used_token_json_auth = True
    else:
        # Default to OAuth first because it supports refresh and local cached tokens.
        if has_oauth_settings or Path(args.token_path).exists():
            oauth = _build_oauth_via_auth_flow(args, prompt_missing=prompt_missing)
        elif token_json:
            oauth = _build_oauth_from_token_json(token_json)
            used_token_json_auth = True
        else:
            oauth = _build_oauth_via_auth_flow(args, prompt_missing=prompt_missing)

    effective_league_key = args.league_key
    preflight_client = YahooApiClient(
        oauth_session=oauth,
        use_cache=not args.disable_cache,
        validate_contracts=False,
    )
    effective_league_key = _resolve_league_key(preflight_client, args.league_key, args.sport)

    try:
        result = run_pipeline(
            league_key=effective_league_key,
            sport=args.sport,
            oauth_session=oauth,
            config=PipelineConfig(
                storage_target=args.storage_target,
                use_cache=not args.disable_cache,
                polars_output_dir=args.polars_output_dir,
                polars_file_format=args.polars_file_format,
                iceberg_catalog=IcebergCatalogConfig(uri=args.iceberg_uri, warehouse=args.iceberg_warehouse),
                iceberg_namespaces=IcebergNamespaceConfig(nfl=args.iceberg_nfl_namespace, nba=args.iceberg_nba_namespace),
                iceberg_idempotency_store=args.iceberg_idempotency_store,
                iceberg_dry_run=args.iceberg_dry_run,
            ),
        )
    except HTTPError as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if used_token_json_auth and status_code == 401:
            print("Token JSON auth returned 401 Unauthorized. Falling back to Yahoo OAuth flow...")
            try:
                oauth = _build_oauth_via_auth_flow(args, prompt_missing=prompt_missing)
            except ValueError as fallback_exc:
                raise ValueError(
                    "Fallback OAuth flow requires Yahoo client credentials. "
                    "Set YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET, and YAHOO_REDIRECT_URI "
                    "(or pass --client-id/--client-secret/--redirect-uri)."
                ) from fallback_exc
            result = run_pipeline(
                league_key=effective_league_key,
                sport=args.sport,
                oauth_session=oauth,
                config=PipelineConfig(
                    storage_target=args.storage_target,
                    use_cache=not args.disable_cache,
                    polars_output_dir=args.polars_output_dir,
                    polars_file_format=args.polars_file_format,
                    iceberg_catalog=IcebergCatalogConfig(uri=args.iceberg_uri, warehouse=args.iceberg_warehouse),
                    iceberg_namespaces=IcebergNamespaceConfig(nfl=args.iceberg_nfl_namespace, nba=args.iceberg_nba_namespace),
                    iceberg_idempotency_store=args.iceberg_idempotency_store,
                    iceberg_dry_run=args.iceberg_dry_run,
                ),
            )
        else:
            raise

    selected_frames = _select_frames(result.frames, args.entities)
    if not selected_frames:
        print("No frames matched the requested --entities filter.")
        print(f"Available frames: {', '.join(sorted(result.frames.keys()))}")
        return

    print(f"Fetched {len(result.frames)} frames for league {result.league_key} ({result.sport}).")
    print("Frame shapes:")
    for name, frame in sorted(result.frames.items()):
        print(f"  {name}: rows={frame.height}, cols={frame.width}")

    if result.polars_outputs:
        print("\nPolars outputs:")
        for name, path in sorted(result.polars_outputs.items()):
            print(f"  {name}: {path}")

    if result.iceberg_outputs:
        print("\nIceberg write results:")
        for item in result.iceberg_outputs:
            print(
                f"  {item.entity} -> {item.table_identifier} "
                f"mode={item.mode} source_rows={item.source_rows} written_rows={item.written_rows} "
                f"skipped={item.skipped_by_idempotency}"
            )

    if args.audit_iceberg and result.iceberg_outputs:
        print("\nIceberg audit:")
        audit_targets = [
            item.table_identifier
            for item in result.iceberg_outputs
            if item.source_rows > 0
        ]
        audit_rows = _audit_iceberg_tables(
            IcebergCatalogConfig(uri=args.iceberg_uri, warehouse=args.iceberg_warehouse),
            audit_targets,
        )
        for identifier, row_count, error in audit_rows:
            if error is not None:
                print(f"  {identifier}: ERROR {error}")
            else:
                print(f"  {identifier}: rows={row_count}")

    with pl.Config(tbl_rows=args.head, tbl_cols=20, fmt_str_lengths=80):
        for name, frame in sorted(selected_frames.items()):
            print("\n" + "=" * 100)
            print(f"{name} preview (top {min(args.head, frame.height)} rows)")
            print("=" * 100)
            if frame.height == 0:
                print("<empty frame>")
                continue
            print(frame.head(args.head))


if __name__ == "__main__":
    main()
