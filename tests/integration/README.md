# integration

Tests that hit real external services: Airtable (`AIRTABLE_API_KEY`/`AIRTABLE_BASE_ID`)
and OpenRouter (`OPENROUTER_API_KEY`). Runs in CI too (see `.github/workflows/ci.yml`),
using GitHub Actions secrets — no mocking of the external service itself.

Locally, `conftest.py` in this directory auto-loads `.env` (`python-dotenv`) so these
run with `uv run pytest tests/integration` directly — no need to `source .env` first.
It never overrides real env vars, so CI (which sets them via secrets, no `.env` file
present) is unaffected.
