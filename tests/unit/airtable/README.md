# airtable

Unit tests for `src/crmToVoice/airtable/` — Airtable calls mocked/faked via
`unittest.mock.patch.object` on each module's `get_table`/`get_records_by_ids` imports, never real.
Real-Airtable coverage lives in `tests/integration/airtable/`.

| File | Purpose |
|---|---|
| `test_client.py` | Unit coverage for `airtable/client.py` — `get_api`, `get_table`, `get_records_by_ids`. |
| `test_leads.py` | Unit coverage for `airtable/leads.py` — create/update/delete/search/get, with `get_table` mocked. |
| `test_imoveis.py` | Unit coverage for `airtable/imoveis.py` — create/update/delete/search/get, with `get_table` mocked. |
| `test_visitas.py` | Unit coverage for `airtable/visitas.py` — create (incl. the `Lead`-required `ValueError`), list-by-lead, with `get_table` mocked. |
