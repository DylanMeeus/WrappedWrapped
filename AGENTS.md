# Repository Guidelines

## Project Structure & Module Organization

- Application code lives in `src/` with CLI entrypoints in `src/cli.py`.
- Notebook exploration lives under `notebooks/`.
- Raw Spotify snapshots are stored under `data/raw/` (ignored by git).
- Static site files live under `web/`.
- Add tests under `tests/` and mirror the `src/` structure when introduced.
- Place static assets in `assets/` and documentation in `docs/` when they are introduced.

## Build, Test, and Development Commands

- Python dependencies are listed in `requirements.txt`.
- Run the CLI with `python src/cli.py` (supports `--year`).
- No test tooling is configured yet; document new commands in `README.md`.

## Coding Style & Naming Conventions

- No formatter or linter is configured.
- Use consistent indentation (2 spaces for JavaScript/TypeScript, 4 spaces for Python) and keep line lengths reasonable (around 100 characters) until tooling is added.
- Prefer clear, descriptive names: `userService`, `parse_config`, `UserProfile`.
- If you introduce a formatter (e.g., Prettier, Black), note the exact version and configuration in the repo.

## Testing Guidelines

- No testing framework is configured.
- When tests are added, mirror code structure (e.g., `src/foo.ts` -> `tests/foo.test.ts`).
- Use descriptive test names that state behavior, such as `returns_empty_list_on_no_input`.

## Commit & Pull Request Guidelines

- Commit history is not available in this repository.
- Use concise, imperative commit messages: `Add user profile schema`.
- Pull requests should include a clear summary, steps to verify, and screenshots for UI changes.

## Agent-Specific Instructions

- Keep this guide updated as the project gains structure and tooling.
- Avoid introducing undocumented commands or conventions.
