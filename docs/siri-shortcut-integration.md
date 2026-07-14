# Siri Shortcut integration — how it actually works

Plain factual reference for building the iPhone side of the flow described in
`docs/Agent.md` and `docs/superpowers/specs/2026-07-14-agent-runtime-design.md`
(request `{session_id, text}`, response `{session_id, reply_text, done}`).
Facts below are sourced from Apple's own Shortcuts documentation and
established community references (linked inline). Anything not confirmed by
a source is marked **unconfirmed**.

## 1. Triggering by voice ("Hey Siri, ...")

- A Shortcut runs by voice when you say its **name** or a **custom trigger
  phrase** you've recorded for it, after "Hey Siri".
- To set a custom phrase: open the shortcut's settings → "Add to Siri" →
  speak (or type) the phrase. You say it **three times** during setup so
  Siri learns your voice for it.
- Apple's own guidance: keep phrases short (2–3 words work best), speak it
  **verbatim** every time, and avoid phrases that could come up in normal
  conversation (they'll misfire).
- If the shortcut's name matches a built-in Siri command, Siri runs the
  shortcut instead of the built-in command.

Source: [Run shortcuts with Siri – Apple Support](https://support.apple.com/guide/shortcuts/run-shortcuts-with-siri-apd07c25bb38/ios), [Siri Human Interface Guidelines – Apple Developer](https://developers.apple.com/design/human-interface-guidelines/siri/overview/shortcuts-and-suggestions/)

## 2. Capturing speech — "Dictate Text" action

- Records audio and converts it to a text variable you can use later in the
  shortcut.
- **Stop Listening** setting has three modes: *After Pause*, *After Short
  Pause*, *On Tap*. This controls when dictation ends and the action
  returns.
  - Community reports say *On Tap* has been unreliable on some iOS versions
    (falls back to pause-based behavior) — **unconfirmed** whether this is
    still true on the iOS version you'll be using; test it.
- **Language**: the action's UI doesn't expose a language picker, but typing
  a locale code (e.g. `pt_PT`) into the language field is reported to work
  and changes what language it listens for. **Unconfirmed** first-hand for
  `pt_PT` specifically — verify hands-on for Portuguese dictation quality.

Source: [Getting It Done with a Shortcut – AppleVis](https://www.applevis.com/blog/getting-it-done-shortcut-ios-12), [Apple Community thread on Stop Listening](https://discussions.apple.com/thread/255582634)

## 3. Calling the webhook — "Get Contents of URL" action

- Supports GET, POST, PUT, PATCH, DELETE, and lets you add custom **Headers**.
- Switching Method to POST reveals a **Request Body** field with three
  modes: JSON, Form, File.
- **JSON mode limitation**: it only supports a top-level JSON **object**
  (`{...}`), not a top-level array. Not an issue for us — our payload
  (`{session_id, text}`) is already a top-level object.
- In JSON mode you add fields as key/value pairs directly in the action's
  UI (key name + value, where the value can be a variable like the
  Dictate Text output).
- Reported quirk: the action sometimes **ignores an explicitly-set
  `Content-Type` header** in JSON mode — test that the webhook receives
  `application/json` as expected, and adjust the webhook's parsing to be
  lenient if not.
- The action's output is the raw response body, which you feed into
  **Get Dictionary Value** (§4) to read `reply_text` / `done`.

Source: [Request your first API – Apple Support](https://support.apple.com/guide/shortcuts/request-your-first-api-apd58d46713f/ios), [Get Contents of URL – Matthew Cassinelli](https://matthewcassinelli.com/actions/get-contents-of-url/)

## 4. Reading the response — "Get Dictionary Value"

- Turns the JSON response into a dictionary you can pull fields from by key
  name (e.g. `reply_text`, `done`).
- If the response isn't automatically treated as a dictionary, run
  **Get Dictionary from Input** on the raw text first, then Get Dictionary
  Value on the result.
- Nested keys are reachable with dot notation — not needed for our flat
  `{session_id, reply_text, done}` shape, but useful to know if the payload
  grows.
- This only works reliably if the webhook actually sends a JSON
  `Content-Type` — see the quirk noted in §3.

Source: [Get Dictionary Value action – Apple Support](https://support.apple.com/guide/shortcuts/get-dictionary-value-action-apdf01294032/ios), [Parsing JSON in Shortcuts – Apple Support](https://support.apple.com/guide/shortcuts/parsing-json-apdde2dfe749/ios)

## 5. Speaking the reply — "Speak Text" action

- Speaks a text variable (`reply_text`) out loud through the device.
- Has a **"Wait Until Finished"** toggle, reachable via "Show More" on the
  action. When on, the shortcut doesn't proceed to the next action until
  speech playback completes — this is what you want before re-opening
  dictation, so the person isn't dictated-over by Siri still talking.
  **Unconfirmed**: the exact default state of this toggle — check it
  explicitly rather than assuming.

Source: [Apple Community – Speak Text / Wait Until Finished](https://discussions.apple.com/thread/250088842)

## 6. The multi-turn loop (done == false)

Shortcuts has **no native "repeat until condition" / "while" action**.
The two built-in loop actions are:
- **Repeat** — runs a block a fixed number of times.
- **Repeat with Each** — runs a block once per item in a list.

Neither fits "keep looping while `done == false`, count unknown in advance."
The standard, documented workaround in the Shortcuts community is:

- Wrap the "speak reply → dictate → POST → parse response" sequence in an
  **If** action checking `done == false`.
- Inside that branch, end the shortcut by calling a **Run Shortcut** action
  that runs **itself** (the same shortcut, by name), passing along
  `session_id` so it continues the same conversation. This is the
  recognized recursive pattern since Shortcuts has no while-loop primitive.
- When `done == true`, skip the recursive call and let the shortcut end
  normally.

This is a community-documented pattern, not an official Apple feature —
**verify hands-on** that self-referential Run Shortcut calls behave as
expected (e.g. don't hit a recursion depth limit for a typical 2–4 turn
wizard exchange).

Source: [Use Repeat actions – Apple Support](https://support.apple.com/guide/shortcuts/use-repeat-actions-apdc11deb2c1/ios), [Repeat / Loop Until condition is met – Automators Talk](https://talk.automators.fm/t/repeat-loop-until-condition-is-met/3813)

## 7. Constraints relevant to this project

- **Plain HTTP to a LAN IP**: this is the biggest open risk for the
  "same Wi-Fi, direct IP" hosting decision in the runtime spec.
  Multiple Shortcuts users report **SSL errors even when attempting plain
  HTTP** to a local server, and it's not clearly settled online whether
  Shortcuts silently upgrades/expects TLS or whether it was a
  configuration issue on their end. **Not confirmed either way — this
  needs a direct hands-on test** (point `Get Contents of URL` at
  `http://<your-lan-ip>:<port>` and see what actually happens) before
  relying on it. Fallback if plain HTTP doesn't work: serve HTTPS locally
  with a self-signed cert (and accept the extra setup of trusting it on
  the phone), or use a tool like `mkcert`/Tailscale that gives you a
  trusted local HTTPS endpoint.
- **Get Contents of URL timeout**: no documented fixed timeout value was
  found in the sources checked — **unconfirmed**, verify hands-on how long
  it waits for a slow response (relevant since a LangGraph run + LLM call
  isn't instant).
- **Background/foreground execution**: Shortcuts run from Siri can execute
  with the phone locked, but long-running or interactive (dictation +
  speak) shortcuts are generally expected to run in the foreground /
  keep the app active during voice interaction. Not deeply verified here —
  **unconfirmed** edge cases (screen lock mid-wizard, phone call
  interrupting, etc.).

## Needs hands-on verification (not resolved by documentation)

- [ ] Does `Get Contents of URL` actually complete a plain **http://**
      request to a local LAN IP, or does it require HTTPS?
- [ ] Does the webhook receive `Content-Type: application/json` correctly
      from the JSON-mode request body, or does it need to tolerate a
      missing/different header?
- [ ] Default state of "Wait Until Finished" on Speak Text.
- [ ] Whether "On Tap" stop-listening on Dictate Text works reliably on the
      iOS version in use.
- [ ] Whether `pt_PT` (or another locale string) actually changes Dictate
      Text's recognition language when typed into the language field.
- [ ] Whether a shortcut calling itself via Run Shortcut (recursion) has any
      practical depth/time limit relevant to a several-turn wizard.
- [ ] Actual timeout Shortcuts allows `Get Contents of URL` to wait for a
      response.
