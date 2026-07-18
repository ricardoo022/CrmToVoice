# src

| File / Folder | Purpose |
|---|---|
| `crmToVoice/` | The installable package — see `crmToVoice/README.md`. |

The real FastAPI adapter is `crmToVoice/webhook.py` (`Dockerfile.webhook` runs
`crmToVoice.webhook:app`). An earlier stray top-level `webhook.py` stub used
to sit here too — it was never meaningful and has been removed.
