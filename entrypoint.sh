#!/bin/sh
set -e

uv run alembic upgrade head
PYTHONPATH=src exec .venv/bin/uvicorn main:app --proxy-headers --forwarded-allow-ips="*" --port 8000 --host 0.0.0.0
