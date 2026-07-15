# airtable

Unit tests for `src/crmToVoice/airtable/` — Airtable calls mocked/faked via
`unittest.mock.patch.object` on each module's `get_table`/`get_records_by_ids`
imports, never real. Real-Airtable coverage lives in `tests/integration/airtable/`.
