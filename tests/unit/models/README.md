# models

Unit tests for `src/crmToVoice/models/` — pure Pydantic models, no I/O, nothing to mock.

| File | Purpose |
|---|---|
| `test_init.py` | Confirms `models/__init__.py` re-exports the intended public models. |
| `test_state.py` | Unit coverage for `AgentState` (`models/state.py`) — defaults, required fields, `Intent`/`TargetEntity` literals. |
| `test_lead_fields.py` | Unit coverage for `LeadFields` (`models/fields.py`) — aliasing, `model_dump(by_alias=True, exclude_none=True)` behavior. |
| `test_property_fields.py` | Unit coverage for `PropertyFields` (`models/fields.py`) — same, for the Imóveis entity. |
| `test_visit_fields.py` | Unit coverage for `VisitFields` (`models/fields.py`) — same, for the Visitas entity. |
| `test_interpretation.py` | Unit coverage for `Interpretation` (`models/interpretation.py`) — the `interpret_speech` structured-output schema. |
