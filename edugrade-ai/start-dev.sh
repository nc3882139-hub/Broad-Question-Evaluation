#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "EduGrade AI backend: http://localhost:8000/docs"
echo "EduGrade AI frontend: http://localhost:5173"
(cd "$ROOT"/backend && EMBEDDING_BACKEND="${EMBEDDING_BACKEND:-hashing}" SENTIMENT_BACKEND="${SENTIMENT_BACKEND:-lexicon}" uvicorn app.main:app --reload --port 8000) &
BACKEND_PID=$!
(cd "$ROOT"/frontend && npm run dev -- --host 0.0.0.0) &
FRONTEND_PID=$!
trap 'kill "$BACKEND_PID" "$FRONTEND_PID"' EXIT
wait