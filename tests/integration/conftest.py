from dotenv import load_dotenv

# Local dev convenience: fills in AIRTABLE_API_KEY/AIRTABLE_BASE_ID etc. from
# .env when running pytest directly. Never overrides real env vars, so CI
# (which sets these via GitHub Actions secrets, no .env file present) is
# unaffected.
load_dotenv()
