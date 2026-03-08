# Run all tests (API + bot)
.PHONY: test
test: test-api test-bot

# API tests (FastAPI, X-API-Key, etc.)
.PHONY: test-api
test-api:
	PYTHONPATH=. python3 -m pytest api/tests -v

# Bot tests (rating calculation, etc.)
.PHONY: test-bot
test-bot:
	cd bot && python3 -m pytest tests -v
