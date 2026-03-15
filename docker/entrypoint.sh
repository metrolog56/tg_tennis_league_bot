#!/bin/sh
set -e
# API on 8000 (exposed). Bot health would use 8000 by default — use 8001 to avoid clash.
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
cd /app/bot && PORT=8001 exec python main.py
