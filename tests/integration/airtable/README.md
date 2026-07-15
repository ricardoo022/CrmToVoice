# airtable

Integration tests for `src/crmToVoice/airtable/` — hit the real Airtable base (`appiFiRN7rzTMqyff`),
no mocking. Every test that creates a record cleans it up afterwards (fixture teardown/`finally`)
so the real CRM base isn't left with orphaned test data.

| File | Purpose |
|---|---|
| `test_leads.py` | Integration coverage for `airtable/leads.py` — create/update/delete/search/get against the real Leads table. |
| `test_imoveis.py` | Integration coverage for `airtable/imoveis.py` — create/update/delete/search/get against the real Imóveis table. |
| `test_visitas.py` | Integration coverage for `airtable/visitas.py` — create/list-by-lead against the real Visitas table. |
