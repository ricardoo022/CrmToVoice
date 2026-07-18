"""Structured-output schema for the `interpret_speech` LLM node.

Design rationale:

- This is the structured-output schema the (not-yet-built) `interpret_speech`
  LLM node (`docs/Agent.md` §9) will be bound to. It's deliberately separate
  from `AgentState` — this is the LLM's *output contract* for one call, not
  the graph's running state. There is no separate router node that copies
  these three values in: `interpret_speech`/Router 2 is the single entry
  point every turn runs through (`docs/Agent.md` §9: "Runs on every turn,
  new or continuing"), and folds this structured output straight into
  `AgentState` itself.
- `extracted_fields` stays a generic `dict[str, Any]` here rather than one of
  `LeadFields`/`PropertyFields`/`VisitFields`, because `target_entity` —
  which determines which of those three field-shapes would even apply — is
  itself part of this same structured output. The LLM can't be asked to
  produce a field shape that depends on a value it's producing in the same
  call. A later epic should re-validate `extracted_fields` into the correct
  `*Fields` model once `target_entity` is known (e.g.
  `LeadFields.model_validate(extracted_fields)` when
  `target_entity == "Lead"`).
- `intent`/`target_entity` reuse the `Intent`/`TargetEntity` `Literal`
  aliases from `state.py` rather than redefining equivalent literals here —
  this is the one intentional cross-file dependency in the `models/`
  package, done specifically to prevent typo drift between `AgentState` and
  this schema (e.g. `"Read"` vs `"read"`).
- `intent`/`target_entity` are `Optional`, default `None` — not because
  they're ever meaningless when set, but to represent `Agent.md` §7's
  "unrecognizable intent (noise, Siri misheard) → asks to repeat, doesn't
  assume" fallback. Both being required `Literal`s would force the LLM to
  always commit to one of the 4 actions, even for unintelligible input,
  which is exactly the guessing §7 rules out. `None` on either is Router 2's
  signal to skip dispatch and ask the person to repeat themselves, instead
  of routing to one of the 4 paths.
- `crm_context` is deliberately *not* a field here, even though
  `interpret_speech` may call `search_leads`/`search_imoveis` while
  producing this output. Per `Agent.md` §9, the node "folds any match into
  `crm_context`" as a separate step from the structured output it
  "returns" — `crm_context` on `AgentState` is populated by the router node
  (from the agent's own tool-call results), not restated by the LLM inside
  this schema. Asking the LLM to retype full Airtable records into a second
  schema field would be redundant and lossy.
"""

from typing import Any

from pydantic import BaseModel, Field

from crmToVoice.models.state import Intent, TargetEntity


class Interpretation(BaseModel):
    """One LLM call's structured interpretation of the user's speech."""

    intent: Intent | None = None
    target_entity: TargetEntity | None = None
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
