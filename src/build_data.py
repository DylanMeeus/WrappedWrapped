import json
from pathlib import Path

import re

from analysis import build_artist_counts, build_artist_year_counts, load_snapshots

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def main() -> None:
    snapshots = [
        snapshot
        for snapshot in load_snapshots()
        if isinstance(snapshot.get("name"), str)
        and re.fullmatch(r"(19|20)\d{2}", snapshot["name"].strip())
    ]
    if not snapshots:
        raise RuntimeError("No snapshots found in data/raw. Run the CLI fetch first.")

    artist_counts = build_artist_counts(snapshots)
    write_json(PROCESSED_DIR / "artist_counts.json", artist_counts)
    print(f"Wrote {len(artist_counts)} artist counts to data/processed/artist_counts.json")

    artist_year_counts = build_artist_year_counts(snapshots)
    write_json(PROCESSED_DIR / "artist_year_counts.json", artist_year_counts)
    print(
        "Wrote "
        f"{len(artist_year_counts)} artist year counts to data/processed/artist_year_counts.json"
    )


if __name__ == "__main__":
    main()
