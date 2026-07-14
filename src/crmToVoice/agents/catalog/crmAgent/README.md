# crmAgent

The four intent paths (`docs/Agent.md` §5):

- `criar.py` — the only path with the missing-field wizard
- `ler.py` — read-only, never writes
- `atualizar.py` — direct field updates, except changing `Estado` (asks "porquê?" first)
- `apagar.py` — always requires explicit confirmation before deleting
