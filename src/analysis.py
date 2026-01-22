import json
from pathlib import Path

RAW_DIR = Path("data") / "raw"


def load_snapshots(raw_dir: Path = RAW_DIR) -> list[dict]:
    if not raw_dir.exists():
        return []

    snapshots: list[dict] = []
    for path in sorted(raw_dir.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                snapshot = json.load(handle)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(snapshot, dict):
            snapshots.append(snapshot)
    return snapshots


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


def build_overlap(snapshots: list[dict]) -> tuple[list[dict], list[dict]]:
    track_years: dict[str, dict] = {}
    artist_years: dict[str, set[int]] = {}

    for snapshot in snapshots:
        year = snapshot.get("year")
        if not isinstance(year, int):
            continue
        tracks = snapshot.get("tracks", [])
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

    duplicates = [
        {"name": entry["name"], "artists": entry["artists"], "years": sorted(entry["years"])}
        for entry in track_years.values()
        if len(entry["years"]) > 1
    ]
    duplicates.sort(key=lambda entry: (-len(entry["years"]), entry["name"]))

    artist_overlap = [
        {"artist": artist, "years": sorted(years)}
        for artist, years in artist_years.items()
        if len(years) > 1
    ]
    artist_overlap.sort(key=lambda entry: (-len(entry["years"]), entry["artist"]))

    return duplicates, artist_overlap


def build_artist_counts(snapshots: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for snapshot in snapshots:
        tracks = snapshot.get("tracks", [])
        for item in tracks:
            track = normalize_track(item)
            if not track:
                continue
            for artist in track["artists"]:
                if not artist:
                    continue
                counts[artist] = counts.get(artist, 0) + 1

    output = [{"artist": artist, "count": count} for artist, count in counts.items()]
    output.sort(key=lambda entry: (-entry["count"], entry["artist"]))
    return output


def build_artist_year_counts(snapshots: list[dict]) -> list[dict]:
    artist_years: dict[str, set[int]] = {}
    for snapshot in snapshots:
        year = snapshot.get("year")
        if not isinstance(year, int):
            continue
        tracks = snapshot.get("tracks", [])
        for item in tracks:
            track = normalize_track(item)
            if not track:
                continue
            for artist in track["artists"]:
                if not artist:
                    continue
                artist_years.setdefault(artist, set()).add(year)

    output = [
        {"artist": artist, "year_count": len(years)}
        for artist, years in artist_years.items()
    ]
    output.sort(key=lambda entry: (-entry["year_count"], entry["artist"]))
    return output
