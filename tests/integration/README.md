# integration

Tests that hit real external services: Airtable (`AIRTABLE_API_KEY`/`AIRTABLE_BASE_ID`) and
OpenRouter (`OPENROUTER_API_KEY`). Runs in CI too (see `.github/workflows/ci.yml`), using GitHub
Actions secrets — no mocking of the external service itself.

| File / Folder | Purpose |
|---|---|
| `conftest.py` | Auto-loads `.env` locally (`python-dotenv`) so `uv run pytest tests/integration` works without manually sourcing anything. Never overrides real env vars, so CI (which sets them via secrets, no `.env` file present) is unaffected. |
| `airtable/` | Integration tests for `src/crmToVoice/airtable/` — see `airtable/README.md`. |
