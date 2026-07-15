# airtable

Integration tests for `src/crmToVoice/airtable/` — hit the real Airtable base
(`appiFiRN7rzTMqyff`), no mocking. Every test that creates a record cleans it
up afterwards (fixture teardown/`finally`) so the real CRM base isn't left
with orphaned test data.
