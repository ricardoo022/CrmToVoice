# integration

Tests that hit real external services: Airtable (`AIRTABLE_API_KEY`/`AIRTABLE_BASE_ID`)
and OpenRouter (`OPENROUTER_API_KEY`). Runs in CI too (see `.github/workflows/ci.yml`),
using GitHub Actions secrets — no mocking of the external service itself.
