# tests

| Folder | Purpose |
|---|---|
| `unit/` | External services mocked/faked. Fast, no credentials needed — see `unit/airtable/README.md`, `unit/models/README.md`. Also covers `agents/catalog/interpret_speech/` (agent + prompt) and `test_webhook.py` (agent mocked). |
| `integration/` | Hits real external services (Airtable, OpenRouter). Runs locally and in CI — see `integration/README.md`. |
