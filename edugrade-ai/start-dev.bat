@echo off
echo EduGrade AI backend: http://localhost:8000/docs
echo EduGrade AI frontend: http://localhost:5173
start "EduGrade backend" cmd /k "cd /d %~dp0backend && set EMBEDDING_BACKEND=hashing&& set SENTIMENT_BACKEND=lexicon&& uvicorn app.main:app --reload --port 8000"
start "EduGrade frontend" cmd /k "cd /d %~dp0frontend && npm run dev -- --host 0.0.0.0"