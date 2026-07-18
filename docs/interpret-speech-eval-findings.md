# `interpret_speech` eval findings (Tag 1 — all-tools agent)

Working log of real-behavior gaps found by running eval against the Tag 1
all-tools agent (real OpenRouter calls, real Airtable fixtures
created/deleted per run, deterministic evaluators). The agent now has all
18 tools (read + write) and responds with free-form text, not structured
output.

This doc tracks what's actually broken so we can work through it one item
at a time. Expect it to get edited/pruned as issues get fixed or re-verified.

**Note:** this replaces the original `interpret-speech-eval-findings.md`
which tracked the read-only router agent (US-GR-03 / pre-Tag-1). The old
agent's findings are preserved in git history; they don't apply to the
all-tools agent since the prompt, tool set, and response format have all
changed.

## Latest run

Ran `make eval-all-tools` twice against the finished US-T1-01/US-T1-02
prompt (`google/gemini-2.5-flash` via OpenRouter), 5 examples each run
(create, read, update, delete, unclear-utterance). Read, delete, and
unclear passed both times. Two real, reproducible gaps found:

1. **Update doesn't reliably skip the confirmation question.** The prompt
   (§3) explicitly says "não perguntes 'posso confirmar?' antes de um
   Update," but on both runs the agent asked ("Posso alterar o estado dele
   para 'Perdido'?") instead of calling `update_lead` directly. 2/2 — not
   just noise.
2. **Create doesn't reliably search before creating.** Run 1 searched, then
   correctly asked for a missing phone number (expected — Telefone is a
   "perguntado se em falta" field, so this wasn't a bug, just an
   under-specified eval example, since fixed). Run 2, with a fully-specified
   utterance, skipped `search_leads` entirely and created directly.

Neither has been fixed yet — both are open, tracked here, not yet turned
into a prompt change. Re-run `make eval-all-tools` after any prompt edit
aimed at these to confirm.

## Known risks (pre-run)

These are behaviors the current prompt might not handle well with write
tools bound — worth paying special attention to during eval:

1. **Duplicate creates** — agent creates a Lead without searching first,
   even though the person mentioned someone who already exists in the CRM
   (confirmed above — see "Latest run" #2)
2. **Delete without confirmation** — agent calls `delete_lead`/`delete_imovel`
   immediately instead of asking "are you sure?" (not observed so far —
   delete passed both eval runs)
3. **Reckless updates** — agent updates a record based on ambiguous input
   (e.g. two "Joãos" in the CRM, picks the wrong one) — not yet covered by
   an eval example
4. **Tool overload** — with 18 tools bound, the LLM may struggle to pick
   the correct one, especially between similar pairs (`search_leads` vs
   `find_lead`, `list_visitas_by_lead` vs `list_visitas_by_date_range`) —
   not observed so far
