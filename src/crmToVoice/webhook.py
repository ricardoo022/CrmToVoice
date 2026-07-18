"""FastAPI adapter for Tag 1 — `POST /webhook`.

Receives already-dictated text from the Siri Shortcut, forwards it to the
`interpret_speech` all-tools agent (`crmToVoice.agents.catalog.interpret_speech`),
and returns the agent's free-form reply. See `docs/Agent.md` (Tag 1 section,
"Webhook contract") and `docs/backlog/epics/epic-04-siri-integration.md`
(US-SI-01) for the authoritative spec.

The system prompt is rendered fresh on every request (not cached alongside
the agent) so the `{{TODAY}}`/`{{WEEKDAY}}` date anchor it embeds is always
today's actual date, not stale from whenever the agent was first built.

The agent itself is stateless (no checkpointer — see `agent.py`), so this
module owns conversation continuity: `_session_history` accumulates each
session's prior messages (keyed by `session_id`) and replays them on every
call, so a follow-up question the agent asked in a previous webhook call
still has context in the next one. In-memory only, no eviction — acceptable
for a single-user local MVP; would need a real store/TTL for anything else.

FastAPI runs sync endpoints like `webhook()` in a thread pool, so two
requests for the same `session_id` (a Shortcut retry, a double-trigger) can
run concurrently. `_session_locks` gives each `session_id` its own lock,
held for the full read-invoke-write cycle, so those requests are serialized
per-session (never clobbering each other's history) while different
sessions still run in parallel. Same no-eviction tradeoff as
`_session_history` — fine for a single-user local MVP.
"""

import logging
import threading
from collections import defaultdict
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from crmToVoice.agents.catalog.interpret_speech import create_interpret_speech_agent
from crmToVoice.agents.catalog.interpret_speech.prompt import render_system_prompt

logger = logging.getLogger(__name__)

app = FastAPI()

_session_history: dict[str, list[BaseMessage]] = defaultdict(list)

_session_locks_guard = threading.Lock()
_session_locks: dict[str, threading.Lock] = {}


def _get_session_lock(session_id: str) -> threading.Lock:
    with _session_locks_guard:
        lock = _session_locks.get(session_id)
        if lock is None:
            lock = threading.Lock()
            _session_locks[session_id] = lock
        return lock


class WebhookRequest(BaseModel):
    session_id: str
    text: str


class WebhookResponse(BaseModel):
    session_id: str
    reply_text: str
    done: bool


@lru_cache(maxsize=1)
def _get_agent():
    """Builds the `interpret_speech` agent once and caches it — same pattern
    as `crmToVoice.config.get_chat_model`.
    """
    return create_interpret_speech_agent()


@app.post("/webhook")
def webhook(request: WebhookRequest) -> WebhookResponse:
    with _get_session_lock(request.session_id):
        history = _session_history[request.session_id]
        messages = [
            SystemMessage(content=render_system_prompt()),
            *history,
            HumanMessage(content=request.text),
        ]

        try:
            result = _get_agent().invoke({"messages": messages})
        except Exception as exc:
            logger.exception("Agent invocation failed for session_id=%s", request.session_id)
            raise HTTPException(status_code=500, detail=f"Agent invocation failed: {exc}") from exc

        reply_text = ""
        for message in reversed(result["messages"]):
            if isinstance(message, AIMessage):
                reply_text = str(message.content)
                break

        # Blank content (e.g. an AIMessage with only tool_calls and no text,
        # or a provider hiccup) is just as unusable to speak aloud as no
        # AIMessage at all — treat both the same way.
        if not reply_text.strip():
            logger.error(
                "Agent produced no usable AIMessage for session_id=%s (messages=%r)",
                request.session_id,
                result["messages"],
            )
            raise HTTPException(status_code=500, detail="Agent did not produce a reply")

        # Drop the system message (rebuilt fresh next call) and remember the
        # rest so the next request in this session has full context.
        _session_history[request.session_id] = [
            m for m in result["messages"] if not isinstance(m, SystemMessage)
        ]

        return WebhookResponse(session_id=request.session_id, reply_text=reply_text, done=True)
