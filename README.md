# CrmToVoice

**Real estate agents don't want to type. They want to talk.**

## The problem

Every time an agent visits a property with a client, meets someone interested in buying a home, or gets a phone call from a lead, that information is supposed to go into a CRM — a system that keeps track of clients, properties, and appointments. In practice, it often doesn't, because stopping to type notes into an app while driving between appointments, or standing in someone's living room, is friction nobody has time for.

A CRM is only useful if the data in it is actually up to date. Today, most of that data never gets entered — not because agents don't care, but because typing while working is a genuine hassle.

## The solution

**CrmToVoice removes that friction entirely. The agent just talks.**

1. **The agent speaks to Siri**, out loud, right after leaving a visit:
   > "Hey Siri, log visit. I was with João Silva at the apartment on Main Street — he liked it but thought it was expensive, I'll send a proposal tomorrow."

2. **The phone transcribes it** (Siri already does this) and sends the text along.

3. **CrmToVoice reads the note like a person would.** It figures out who the client is, which property is being discussed, what happened, and how the client seemed to feel about it — and writes all of that into the CRM automatically. No forms, no typing, no app to open.

4. If anything important is missing — like a phone number for a brand-new lead — **the assistant asks a quick follow-up question out loud**, and the agent just answers by voice. It only asks about what's actually missing, never a whole form's worth of questions.

5. The agent can also **ask questions and get spoken answers**:
   > "Hey Siri, what visits do I have today?"
   > *"You have 2 visits today: João at 3pm and Maria at 5pm."*

That's the whole idea: say what happened, get it recorded; ask what you need to know, get told. No screens, no typing, no interrupting your day. CrmToVoice bets on a simple idea: if updating the CRM is as easy as talking to a friend, agents will actually do it.

## What it can do

- **Log a visit or phone call**, including what was discussed and how the client reacted
- **Create a new lead** (a potential client) from a quick voice description
- **Update a client's status** — e.g. "the Smiths are no longer interested" or "Ana closed the deal"
- **Set a reminder or next step** — "reminder: call João tomorrow"
- **Link a client to a property** they're interested in
- **Answer questions out loud** — today's schedule, a client's status, how many deals are in negotiation, what the next step is with someone
- **Delete a record** — but only after asking "are you sure?" out loud and getting a clear "yes"

## Who this is for

Field real estate agents who spend their day visiting properties and meeting clients rather than sitting at a desk — whose CRM today only gets updated when they finally find ten spare minutes at the end of the day, if at all.

## Where this is headed

Right now this is **Tag 1** — the quickest, simplest version we could build that a real agent could actually use: one voice-driven AI agent with direct read/write access to the CRM, and a webhook that Siri talks to. It's deliberately simple: single-turn, no multi-step confirmation flow, no wizard — the agent just does its best with what it's given.

**Tag 2** is the planned next step: a proper multi-turn conversation graph with explicit confirmation before destructive actions, a guided wizard for creating records with missing information, and more structured, predictable behavior overall. Tag 1 exists to get something real into an agent's hands as fast as possible and learn from it before building that more robust version.

## Status

This project is being built piece by piece:

- **Done** — the data layer: the part that actually reads and writes to the CRM.
- **Done** — the "brain": a single agent (Tag 1) that understands what was said and acts on the CRM directly (create/read/update/delete), plus the webhook that exposes it over HTTP.
- **In progress** — quality: an eval suite already caught a couple of real gaps (e.g. the agent doesn't *always* search before creating, or *always* skip asking for confirmation on an update) that are being worked through.
- **Not started yet** — the Siri connection itself: the iPhone Shortcut that actually dictates to the webhook and speaks the reply back.

For technical details (how it's built, how to run it) see `CLAUDE.md`. For the full product design, see the `docs/` folder.

## Stack

- **Python** with **uv** as the package manager
- **LangChain** / **LangGraph** for the agent itself and its tools
- **LangSmith** for tracing and evals
- An OpenRouter-served LLM as the agent's model
- **Airtable** (via `pyairtable`) as the CRM/database
- **FastAPI** + **Uvicorn** for the webhook that Siri talks to
- **Pydantic** for structured data
- **Ruff**, **Pyright**, and **pytest** for linting, type checking, and tests

---

*This project speaks Portuguese, since it's built for a Portuguese-speaking real estate agent — the examples above are translated for clarity.*
