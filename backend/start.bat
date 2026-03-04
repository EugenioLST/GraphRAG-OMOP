@echo off
REM ============================================================================
REM GraphRAG-OMOP Backend API - Startup Script
REM ============================================================================

echo.
echo ========================================
echo   GraphRAG-OMOP Backend API
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please create it first:
    echo   python -m venv venv
    echo   call venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/3] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo       OK
echo.

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Please create .env with:
    echo   OPENAI_API_KEY=your_key_here
    echo.
    pause
)

REM Check if embeddings exist
if not exist "data\embeddings\embeddings.npy" (
    echo [WARNING] Embeddings not found!
    echo Please generate them first:
    echo   python -m src.phase2.embeddings --max-concepts 100000
    echo.
    pause
)

echo [2/3] Starting FastAPI server...
echo.
echo       Backend URL: http://localhost:8000
echo       API Docs:    http://localhost:8000/docs
echo       Health:      http://localhost:8000/health
echo       Status:      http://localhost:8000/status
echo.
echo [INFO] Grafo will load in background (~15-30 seconds)
echo [INFO] Check /status endpoint to see when ready
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server
echo [3/3] Running server...
echo ========================================
echo.
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

REM If server stops
echo.
echo ========================================
echo Server stopped.
echo ========================================
pause
