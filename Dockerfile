# Combined image: API (FastAPI) + Bot (Telegram). One container, one Koyeb service.
FROM python:3.12-slim

WORKDIR /app

# Dependencies: API and bot (copy under distinct names so both are kept)
COPY api/requirements.txt ./api-requirements.txt
COPY bot/requirements.txt ./bot-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt -r bot-requirements.txt

# Application code
COPY api ./api
COPY bot ./bot

# Entrypoint: run API on 8000, bot in foreground (bot health on 8001 to avoid port clash)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["/entrypoint.sh"]
