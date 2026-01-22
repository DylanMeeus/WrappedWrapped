import base64
import json
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

ACCOUNTS_BASE_URL = "https://accounts.spotify.com"
API_BASE_URL = "https://api.spotify.com/v1"


@dataclass
class OAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    token_path: str


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    code = None
    error = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            OAuthCallbackHandler.code = params["code"][0]
            message = "Authorization received. You can close this tab."
            self.send_response(200)
        else:
            OAuthCallbackHandler.error = params.get("error", ["unknown"])[0]
            message = "Authorization failed. Check the CLI for details."
            self.send_response(400)

        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format, *args):
        return


def load_token(token_path: str) -> dict | None:
    try:
        with open(token_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return None


def save_token(token_path: str, token: dict) -> None:
    with open(token_path, "w", encoding="utf-8") as handle:
        json.dump(token, handle, indent=2, sort_keys=True)


def token_is_valid(token: dict) -> bool:
    return token.get("expires_at", 0) > time.time() + 60


def build_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


def request_token(data: dict, client_id: str, client_secret: str) -> dict:
    headers = {
        "Authorization": f"Basic {build_auth_header(client_id, client_secret)}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        f"{ACCOUNTS_BASE_URL}/api/token",
        data=data,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    token = response.json()
    token["expires_at"] = int(time.time()) + token.get("expires_in", 0)
    return token


def wait_for_auth_code(redirect_uri: str, timeout_seconds: int = 180) -> str:
    parsed = urlparse(redirect_uri)
    server = HTTPServer((parsed.hostname, parsed.port), OAuthCallbackHandler)
    server.timeout = 1
    start = time.time()

    while time.time() - start < timeout_seconds:
        server.handle_request()
        if OAuthCallbackHandler.code:
            return OAuthCallbackHandler.code
        if OAuthCallbackHandler.error:
            raise RuntimeError(f"Authorization error: {OAuthCallbackHandler.error}")

    raise TimeoutError("Timed out waiting for Spotify authorization.")


def authorize(config: OAuthConfig) -> dict:
    query = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": config.redirect_uri,
        "scope": " ".join(config.scopes),
    }
    url = f"{ACCOUNTS_BASE_URL}/authorize?{urlencode(query)}"
    print("Open this URL in a browser to authorize:")
    print(url)

    code = wait_for_auth_code(config.redirect_uri)
    token = request_token(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.redirect_uri,
        },
        config.client_id,
        config.client_secret,
    )
    if "refresh_token" not in token:
        raise RuntimeError("Spotify did not return a refresh token. Try again.")
    save_token(config.token_path, token)
    return token


def refresh_token(config: OAuthConfig, refresh_token_value: str) -> dict:
    token = request_token(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token_value,
        },
        config.client_id,
        config.client_secret,
    )
    token["refresh_token"] = refresh_token_value
    save_token(config.token_path, token)
    return token


def get_access_token(config: OAuthConfig) -> str:
    token = load_token(config.token_path)
    if token and token_is_valid(token):
        return token["access_token"]
    if token and token.get("refresh_token"):
        token = refresh_token(config, token["refresh_token"])
        return token["access_token"]
    token = authorize(config)
    return token["access_token"]


def spotify_get(url: str, access_token: str) -> dict:
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_all_items(url: str, access_token: str) -> list[dict]:
    items: list[dict] = []
    while url:
        payload = spotify_get(url, access_token)
        items.extend(payload.get("items", []))
        url = payload.get("next")
    return items


def get_user_playlists(access_token: str) -> list[dict]:
    return fetch_all_items(f"{API_BASE_URL}/me/playlists?limit=50", access_token)


def get_playlist_tracks(access_token: str, playlist_id: str) -> list[dict]:
    url = f"{API_BASE_URL}/playlists/{playlist_id}/tracks?limit=100"
    return fetch_all_items(url, access_token)
