import argparse
import json
import os
import re
from pathlib import Path

from spotify_api import (
    OAuthConfig,
    get_access_token,
    get_current_user,
    get_playlist_tracks,
    get_user_playlists,
    search_playlists,
)

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
TOKEN_PATH = DATA_DIR / "spotify_token.json"
YEAR_START = 2017
YEAR_END = 2025


def parse_year_from_name(name: str) -> int | None:
    cleaned = name.strip()
    if re.fullmatch(r"(19|20)\d{2}", cleaned):
        return int(cleaned)
    return None


def normalize_track(item: dict) -> dict | None:
    track = item.get("track")
    if not track:
        return None
    artists = [artist.get("name", "") for artist in track.get("artists", [])]
    return {
        "id": track.get("id"),
        "uri": track.get("uri"),
        "name": track.get("name"),
        "artists": artists,
        "album": (track.get("album") or {}).get("name"),
        "added_at": item.get("added_at"),
    }


def build_config() -> OAuthConfig:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/callback")
    scopes = ["playlist-read-private", "playlist-read-collaborative"]

    if not client_id or not client_secret:
        raise RuntimeError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in your environment.")

    return OAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scopes=scopes,
        token_path=str(TOKEN_PATH),
    )


def filter_playlists(
    playlists: list[dict],
    year: int | None,
    year_start: int,
    year_end: int,
) -> list[dict]:
    matched = []
    for playlist in playlists:
        playlist_name = playlist.get("name", "")
        playlist_year = parse_year_from_name(playlist_name)
        if not playlist_year:
            continue
        if year and playlist_year != year:
            continue
        if playlist_year < year_start or playlist_year > year_end:
            continue
        matched.append({"year": playlist_year, **playlist})
    return matched


def save_playlist_snapshot(playlist: dict, tracks: list[dict]) -> Path:
    snapshot = {
        "id": playlist.get("id"),
        "name": playlist.get("name"),
        "year": playlist.get("year"),
        "tracks": tracks,
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{playlist.get('id')}.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(snapshot, handle, indent=2, sort_keys=True)
    return path


def summarize(playlists: list[dict], playlist_tracks: dict[str, list[dict]]) -> None:
    track_years: dict[str, dict] = {}
    artist_years: dict[str, set[int]] = {}

    for playlist in playlists:
        year = playlist.get("year")
        tracks = playlist_tracks.get(playlist.get("id"), [])
        artists_in_playlist = set()

        for item in tracks:
            track = normalize_track(item)
            if not track:
                continue
            artists_in_playlist.update(track["artists"])
            key = track["id"] or f"{track['name']}|{'/'.join(track['artists'])}"
            entry = track_years.setdefault(
                key,
                {
                    "name": track["name"],
                    "artists": track["artists"],
                    "years": set(),
                },
            )
            entry["years"].add(year)

        for artist in artists_in_playlist:
            artist_years.setdefault(artist, set()).add(year)

        print(
            f"{playlist.get('name')} ({year}): {len(tracks)} tracks, "
            f"{len(artists_in_playlist)} artists"
        )

    duplicates = [entry for entry in track_years.values() if len(entry["years"]) > 1]
    duplicates.sort(key=lambda entry: (-len(entry["years"]), entry["name"]))

    artist_overlap = [
        {"artist": artist, "years": years}
        for artist, years in artist_years.items()
        if len(years) > 1
    ]
    artist_overlap.sort(key=lambda entry: (-len(entry["years"]), entry["artist"]))

    print("\nOverlap highlights")
    print(f"Tracks appearing in multiple years: {len(duplicates)}")
    for entry in duplicates[:10]:
        years = ", ".join(str(year) for year in sorted(entry["years"]))
        artists = ", ".join(entry["artists"]) or "Unknown artist"
        print(f"- {entry['name']} — {artists} ({years})")

    print(f"\nArtists appearing in multiple years: {len(artist_overlap)}")
    for entry in artist_overlap[:10]:
        years = ", ".join(str(year) for year in sorted(entry["years"]))
        print(f"- {entry['artist']} ({years})")


def fetch_command(year: int | None) -> None:
    config = build_config()
    access_token = get_access_token(config)

    playlists = get_user_playlists(access_token)
    matched = filter_playlists(playlists, year, YEAR_START, YEAR_END)

    if not matched:
        print(
            "No playlists matched your criteria for years "
            f"{YEAR_START} to {YEAR_END}."
        )
        print(f"Playlists found: {len(playlists)}")
        print("\nAll playlists:")
        for playlist in playlists:
            name = playlist.get("name", "Unnamed playlist")
            playlist_id = playlist.get("id", "unknown-id")
            owner = (playlist.get("owner") or {}).get("display_name", "unknown owner")
            print(f"- {name} ({playlist_id}) by {owner}")
        return

    playlist_tracks: dict[str, list[dict]] = {}
    for playlist in matched:
        playlist_id = playlist.get("id")
        tracks = get_playlist_tracks(access_token, playlist_id)
        playlist_tracks[playlist_id] = tracks
        path = save_playlist_snapshot(playlist, tracks)
        print(f"Saved {playlist.get('name')} to {path}")

    print("")
    summarize(matched, playlist_tracks)


def search_command(query: str) -> None:
    config = build_config()
    access_token = get_access_token(config)
    user = get_current_user(access_token)
    user_id = user.get("id")
    playlists = search_playlists(access_token, query)

    if not playlists:
        print("No playlists matched your search.")
        return

    if not user_id:
        raise RuntimeError("Unable to determine the current user ID.")

    owned_playlists = [
        playlist
        for playlist in playlists
        if isinstance(playlist, dict)
        and (playlist.get("owner") or {}).get("id") == user_id
    ]

    if not owned_playlists:
        print("No owned playlists matched your search.")
        return

    print(f"Owned playlists matching '{query}':")
    for playlist in owned_playlists:
        if not isinstance(playlist, dict):
            print(f"- Unexpected playlist entry: {playlist!r}")
            continue
        name = playlist.get("name", "Unnamed playlist")
        playlist_id = playlist.get("id", "unknown-id")
        owner = (playlist.get("owner") or {}).get("display_name", "unknown owner")
        print(f"- {name} ({playlist_id}) by {owner}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Spotify Top Songs playlists.")
    parser.add_argument(
        "--year",
        type=int,
        help="Only include playlists for a specific year (e.g. 2018).",
    )
    parser.add_argument(
        "--search",
        help="Search Spotify for playlists by name (e.g. 'Your Top Songs 2024').",
    )
    args = parser.parse_args()

    if args.search:
        search_command(args.search)
        return

    fetch_command(args.year)


if __name__ == "__main__":
    main()
