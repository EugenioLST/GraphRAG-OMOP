@echo off
REM GraphRAG-OMOP Backend - FastAPI Server

echo Starting GraphRAG-OMOP Backend...
echo.

call venv\Scripts\activate.bat

echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Grafo loading in background (~15-30s). Check /status
echo Press Ctrl+C to stop
echo.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
