# WrappedWrapped

Analyze your Spotify "Your Top Songs" playlists across years. Start by fetching playlist data
and printing overlap highlights on the CLI.

## Setup

1. Create a Spotify app at https://developer.spotify.com/dashboard and add a redirect URI
   (default used here: `http://127.0.0.1:8080/callback`).
2. Export credentials:

```bash
export SPOTIFY_CLIENT_ID="your-client-id"
export SPOTIFY_CLIENT_SECRET="your-client-secret"
export SPOTIFY_REDIRECT_URI="http://127.0.0.1:8080/callback"
```

3. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Fetch Top Songs playlists

```bash
python src/cli.py
```

To scope to a specific year:

```bash
python src/cli.py --year 2018
```

To search Spotify for playlists by name:

```bash
python src/cli.py --search "Your Top Songs 2024"
```

CLI output includes playlist summaries plus overlap highlights. Raw snapshots are saved
under `data/raw/` (ignored by git). By default, the CLI targets playlists named by year
between 2017 and 2025 (inclusive).
