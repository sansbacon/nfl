"""Authentication interfaces for Yahoo Fantasy API access."""

from __future__ import annotations

import json
import logging
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from requests_oauthlib import OAuth2Session

AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
SCOPES = ["fspt-r"]

logger = logging.getLogger(__name__)


def load_token(token_path: Path) -> dict | None:
    if not token_path.exists():
        return None
    return json.loads(token_path.read_text(encoding="utf-8"))


def save_token(token_path: Path, token: dict) -> None:
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")


def extract_auth_code(raw_input: str) -> str:
    text = (raw_input or "").strip()
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        parsed = urlparse(text)
        return parse_qs(parsed.query).get("code", [""])[0].strip()
    if "code=" in text:
        query_like = text[1:] if text.startswith("?") else text
        return parse_qs(query_like).get("code", [""])[0].strip()
    if "&state=" in text:
        return text.split("&state=", 1)[0].strip()
    return text


def build_oauth_session(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    token_path: Path,
    auth_code: str | None,
    open_browser: bool,
) -> OAuth2Session:
    token = load_token(token_path)

    def token_updater(new_token: dict) -> None:
        save_token(token_path, new_token)

    oauth = OAuth2Session(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        token=token,
        auto_refresh_url=TOKEN_URL,
        auto_refresh_kwargs={"client_id": client_id, "client_secret": client_secret},
        token_updater=token_updater,
    )

    if token:
        return oauth

    authorization_url, _state = oauth.authorization_url(AUTH_URL)
    logger.info("No cached Yahoo OAuth token found")
    logger.info("Authorize via URL: %s", authorization_url)

    if open_browser:
        webbrowser.open(authorization_url)

    code = extract_auth_code(auth_code or "")
    if not code:
        raise ValueError(
            "No OAuth token cache and no auth_code provided. Pass auth_code from Yahoo redirect URL."
        )

    try:
        new_token = oauth.fetch_token(
            TOKEN_URL,
            code=code,
            client_id=client_id,
            client_secret=client_secret,
            include_client_id=True,
        )
    except Exception as exc:
        raise RuntimeError(
            "Yahoo OAuth token exchange failed. Verify redirect URI match and use a fresh code."
        ) from exc

    save_token(token_path, new_token)
    return oauth
