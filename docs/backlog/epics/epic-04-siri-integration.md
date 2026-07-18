
# Epic 04 — Tag 1: Siri Integration

**Status:** 🔲 Not started

**Goal:** Expose the all-tools `interpret_speech` agent (Epic 03) to the
outside world — a webhook the Siri Shortcut can call, and a Shortcut that
actually round-trips voice to CRM and back. Simple wiring, no new agent
logic.

**Depends on:**

- Epic 03 (`agents/catalog/interpret_speech/`) — the all-tools agent

---

## US-SI-01 — Build webhook (FastAPI POST /webhook)

As a developer
I want a FastAPI webhook at `POST /webhook` that receives
`{session_id, text}` and returns `{session_id, reply_text, done}`
So that the Siri Shortcut has an endpoint to call

**Acceptance Criteria:**

- [ ] `POST /webhook` accepts `{"session_id": str, "text": str}` JSON body
- [ ] On each request, the webhook builds a message list: a `SystemMessage`
      with the rendered system prompt, plus a `HumanMessage` with the
      current `text`
- [ ] The webhook instantiates the agent (cached, created once) and calls
      `agent.invoke({"messages": messages})`
- [ ] The agent's response (the last `AIMessage` content) is returned as
      `reply_text` in `{"session_id": ..., "reply_text": ..., "done": true}`
- [ ] `done` is always `true` (Tag 1 is single-turn; multi-turn is Tag 2)
- [ ] Errors (agent failure, timeout) return HTTP 500 with a descriptive
      message body
- [ ] The webhook runs at `0.0.0.0:8000`, served via `uvicorn`
- [ ] The `.env` variables (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`,
      `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`) are loaded and available
- [ ] Integration test: start the webhook, `POST` a realistic utterance,
      assert `reply_text` is a non-empty string and `done` is `true`

---

## US-SI-02 — Test end-to-end with Siri Shortcut

As a user
I want to say "Hey Siri, [CRM command]" and have the CRM updated and Siri
read the reply out loud
So that I can use the system hands-free

**Acceptance Criteria:**

- [ ] iPhone Shortcut exists that:
      1. Accepts voice trigger phrase (e.g. "CRM")
      2. Dictates the spoken text
      3. `POST`s `{"session_id": <uuid>, "text": <dictated>}` to the webhook
      4. Parses the JSON response
      5. Speaks `reply_text` out loud
- [ ] Full round-trip tested with real utterances:
      - "Novo lead. Maria Costa, quer um apartamento até 250 mil."
      - "Qual é o estado do João?"
      - "O Zé já não está interessado."
      - "Apaga o lead da Maria."
- [ ] The Shortcut connects to the webhook via LAN IP (tested: plain HTTP
      works from Shortcuts, or HTTPS with self-signed cert as fallback)
- [ ] Documented in `docs/siri-shortcut-integration.md`

---

## Open notes for review

- These two stories were originally US-T1-03/US-T1-04 inside Epic 03.
  Split out because they're pure wiring — no agent logic changes — once
  Epic 03's agent works, this epic should be quick.
