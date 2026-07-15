# src

| File / Folder | Purpose |
|---|---|
| `crmToVoice/` | The installable package — see `crmToVoice/README.md`. |
| `webhook.py` (empty stub) | Not the FastAPI adapter — that lives at `crmToVoice/webhook.py` per the architecture (`Dockerfile.webhook` expects `crmToVoice.webhook:app`). This stray top-level file isn't meaningful; don't assume it is. |
