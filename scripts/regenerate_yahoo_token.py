#!/usr/bin/env python3
"""Regenerate Yahoo OAuth token JSON for local development.

This script reads OAuth client credentials from a JSON file, generates the
Yahoo authorization URL, prompts for the redirect URL/code, exchanges the code
for a token, and writes the token JSON to disk.
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from requests_oauthlib import OAuth2Session
from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nfl.yahoo_fantasy.auth import (  # noqa: E402
    AUTH_URL,
    TOKEN_URL,
    SCOPES,
    extract_auth_code,
    save_token,
)


def _load_credentials(credentials_path: Path, env_path: Path) -> tuple[str, str, str]:
    creds: dict[str, str] = {}
    if credentials_path.exists():
        raw = json.loads(credentials_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Credentials file must contain a JSON object.")
        creds = {
            "client_id": str(raw.get("client_id", "")).strip(),
            "client_secret": str(raw.get("client_secret", "")).strip(),
            "redirect_uri": str(raw.get("redirect_uri", "")).strip(),
        }

    env_values: dict[str, str] = {}
    if env_path.exists():
        loaded = dotenv_values(env_path)
        env_values = {str(k): str(v) for k, v in loaded.items() if v is not None}

    client_id = env_values.get("YAHOO_CLIENT_ID", creds.get("client_id", "")).strip()
    client_secret = env_values.get("YAHOO_CLIENT_SECRET", creds.get("client_secret", "")).strip()
    redirect_uri = env_values.get("YAHOO_REDIRECT_URI", creds.get("redirect_uri", "")).strip()

    missing: list[str] = []
    if not client_id:
        missing.append("client_id")
    if not client_secret:
        missing.append("client_secret")
    if not redirect_uri:
        missing.append("redirect_uri")

    if missing:
        raise ValueError(
            "Missing required OAuth settings. Set YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET, "
            "YAHOO_REDIRECT_URI in .env (or provide client_id/client_secret/redirect_uri in credentials.json). "
            "Missing field(s): "
            + ", ".join(missing)
        )

    return client_id, client_secret, redirect_uri


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate .secrets/yahoo_token.json using Yahoo OAuth authorization code flow."
    )
    parser.add_argument(
        "--credentials",
        default=str(ROOT / ".secrets" / "credentials.json"),
        help="Path to credentials JSON (default: .secrets/credentials.json). Optional when .env has Yahoo values.",
    )
    parser.add_argument(
        "--env-file",
        default=str(ROOT / ".env"),
        help="Path to .env file (default: .env)",
    )
    parser.add_argument(
        "--token",
        default=str(ROOT / ".secrets" / "yahoo_token.json"),
        help="Path to token JSON output (default: .secrets/yahoo_token.json)",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the Yahoo authorization URL in your default browser.",
    )
    args = parser.parse_args()

    credentials_path = Path(args.credentials).resolve()
    env_path = Path(args.env_file).resolve()
    token_path = Path(args.token).resolve()

    client_id, client_secret, redirect_uri = _load_credentials(credentials_path, env_path)

    oauth = OAuth2Session(client_id=client_id, redirect_uri=redirect_uri, scope=SCOPES)
    authorization_url, _state = oauth.authorization_url(AUTH_URL)

    print("Open this URL in your browser and authorize the app:")
    print(authorization_url)
    print()
    print("After redirect, paste either:")
    print("1) the full redirected URL, or")
    print("2) just the code value")

    if args.open_browser:
        webbrowser.open(authorization_url)

    raw_input_value = input("Authorization response: ").strip()
    code = extract_auth_code(raw_input_value)
    if not code:
        raise ValueError("No authorization code detected from your input.")

    token = oauth.fetch_token(
        TOKEN_URL,
        code=code,
        client_id=client_id,
        client_secret=client_secret,
        include_client_id=True,
    )

    save_token(token_path, token)
    print(f"Token saved to: {token_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
