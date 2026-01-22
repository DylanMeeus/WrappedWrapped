# Project Status

## What exists now

- Spotify CLI to fetch yearly playlists (named exactly as years) and save raw snapshots
  under `data/raw/`.
- Caching: years already in `data/raw/` are not re-downloaded.
- Analysis helpers in `src/analysis.py` for overlaps and artist counts.
- Notebook scaffold in `notebooks/analysis.ipynb` that loads snapshots and prints overlap
  highlights.
- Static frontend in `web/` with D3 histograms for artist track counts and yearly
  presence (top 80).

## How to run

1. Fetch playlists and snapshots:

```bash
python src/cli.py
```

2. Build processed chart data:

```bash
python src/build_data.py
```

3. View the site:

```bash
python -m http.server
```

Open `http://localhost:8000/web/`.

## Current assumptions

- Playlists are named exactly as the year (e.g., `2017`, `2018`, ...).
- Target year range is 2017 through 2025.
- Redirect URI defaults to `http://127.0.0.1:8080/callback`.

## Next ideas

- Add filters (year range, artist search, top-N slider) to the Plotly view.
- Add filters (year range, artist search, top-N slider) to the D3 views.
- Add genre drift analysis (requires artist genre enrichment).
- Generate per-year stats for additional charts.
