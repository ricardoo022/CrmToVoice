# Epic 01 — Database (Airtable)

**Status: ✅ Done (2026-07-15).** Implemented in `src/crmToVoice/airtable/`
(`client.py`, `leads.py`, `imoveis.py`, `visitas.py`), with unit tests
(mocked) in `tests/unit/airtable/` and integration tests (real Airtable,
with automatic cleanup of created records) in `tests/integration/airtable/`.
`make check` and `make test` pass: lint, typecheck, 31 unit tests, 18
integration tests.

**Goal:** have the data-access functions over the Airtable base "CRM
Imobiliário (Voz)" (`appiFiRN7rzTMqyff`), so that the agent (Epic 02)
never talks to the Airtable API directly — only through functions already
built to create, read, update, delete, and search records.

**Out of scope for this epic:** intent classification, the question
wizard, the LangGraph graph, the checkpointer, the webhook. Those belong
to Epic 02 (Agent) and Epic 03 (Webhook), which consume what's built here.

**Current state (verified against Airtable, 2026-07-15):** the base
already exists and its three tables (Leads, Imóveis, Visitas) already have
exactly the fields described in `docs/CRM.md` §1. There's no schema-design
work in this epic — only the access functions.

> Note on naming: the module/function names below (`imoveis.py`,
> `visitas.py`, `create_imovel`, `search_leads(nome)`, etc.) use Portuguese
> entity names because that's what they were written and tested against —
> renaming them is a source-code refactor of already-shipped, CI-passing
> work, not a documentation change, so it's tracked separately rather than
> done silently as part of translating this doc to English.

---

## US-DB-01 — Connection to the Airtable base

As a developer
I want to configure authenticated access to the Airtable base from code
So that any future feature can read/write to the base without repeating
authentication logic

**Acceptance Criteria:**

- [x] The Airtable access token (Personal Access Token) is read from an
      environment variable — never hardcoded in code nor committed
      (`client.get_api()`, reads `AIRTABLE_API_KEY` via `os.environ`)
- [x] `.env.example` documents the required variables (e.g.
      `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`)
- [x] There's a single connection function/client to the base, reused by
      every other data-access function (`client.get_table()`, cached via
      `get_api()`; `leads.py`/`imoveis.py`/`visitas.py` all go through
      this)

---

## US-DB-02 — Leads repository (create / read / update / delete / search)

As a developer
I want functions that create, read, update, delete, and search Leads
So that the agent never builds Airtable calls by hand — it only calls
these functions

**Acceptance Criteria:**

- [x] Function to create a Lead, accepting any field from `docs/CRM.md`
      §1.1 (`leads.create_lead`)
- [x] Function to update an existing Lead by ID, accepting any field on
      the table — including fields that are "automatic" at creation time
      (`Estado`/Status, `Sentimento`/Sentiment, `Data Última
      Interação`/Last Interaction Date); that classification
      (`docs/CRM.md` §3) only governs the creation wizard, it doesn't
      limit what this function can write (updating `Estado`/Status is a
      supported action — §2.3) (`leads.update_lead`)
- [x] Function to delete a Lead by ID (`leads.delete_lead`)
- [x] Function to search Leads by name (case-insensitive, partial match),
      returning a list of matches (`leads.search_leads`)
- [x] Function to read a Lead by ID, including its associated Visits
      (`leads.get_lead`)

---

## US-DB-03 — Properties repository (create / read / update / delete / search)

As a developer
I want functions that create, read, update, delete, and search Properties
(*Imóveis*)
So that the agent never builds Airtable calls by hand for Properties

**Acceptance Criteria:**

- [x] Function to create a Property, accepting any field from
      `docs/CRM.md` §1.2 (`imoveis.create_imovel`)
- [x] Function to update an existing Property by ID, accepting any field
      on the table — including `Estado`/Status (automatic at creation,
      but explicitly updatable by voice — §2.6b) (`imoveis.update_imovel`)
- [x] Function to delete a Property by ID (`imoveis.delete_imovel`)
- [x] Function to search Properties by address (case-insensitive, partial
      match), returning a list of matches (`imoveis.search_imoveis`)
- [x] Function to read a Property by ID, including its associated Visits
      (`imoveis.get_imovel`)

---

## US-DB-04 — Visits repository (create / read / update / delete / query)

As a developer
I want functions that create, read, update, delete, and query Visits
(*Visitas*), including by date and by associated Lead
So that this supports logging visits, correcting a wrongly logged visit
(§2.12), and the voice read/query questions (§2.8–2.11)

**Acceptance Criteria:**

- [x] Function to create a Visit, linking it to a Lead (required) and
      optionally to a Property, accepting any field from `docs/CRM.md`
      §1.3 (`visitas.create_visita`, validates that `Lead` isn't empty
      and raises `ValueError` otherwise)
- [x] Function to update an existing Visit by ID, accepting any field on
      the table — including reassigning the `Lead`/`Imóvel` link fields
      (§2.7 "link a lead to a property") (`visitas.update_visita`)
- [x] Function to delete a Visit by ID (voice confirmation before calling
      this function is Epic 02's responsibility, not this function's)
      (`visitas.delete_visita`)
- [x] Function to read a Visit by ID (`visitas.get_visita`)
- [x] Function to list Visits within a date range (supports "what visits
      do I have today?") (`visitas.list_visitas_by_date_range`)
- [x] Function to list Visits associated with a specific Lead, ordered by
      date (supports "what's the next step with Maria?")
      (`visitas.list_visitas_by_lead`)

---

## Open notes for review

- **Search by name/address:** implemented as case-insensitive partial
  matching (Airtable formula `SEARCH(LOWER(...), LOWER(...))`). Still
  undecided whether this is enough, or whether dictation/spelling errors
  (accents, phonetic variants) need handling — not yet tested with real
  dictation.
- No story here covers the Context Middleware itself (resolving
  Lead/Property mentions in the text before the LLM runs, or what to do
  with multiple search results) — that belongs to Epic 02, using the
  search functions built here.
- Field validation, API error handling, and pagination remain out of
  scope, as planned. Test-data isolation has no formal strategy (there's
  no sandbox Airtable base — integration tests run against the real one),
  but every test that creates a record cleans it up afterwards
  (`cleanup`/`finally` fixture); confirmed no orphaned records after
  several runs.
