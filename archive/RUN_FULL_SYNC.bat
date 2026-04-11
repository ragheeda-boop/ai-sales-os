@echo off
chcp 65001 >nul 2>&1
title AI Sales OS — Full Pipeline Run
color 0A

echo ══════════════════════════════════════════════════════════════
echo   AI Sales OS — Full Local Pipeline Run
echo   Mirrors: GitHub Actions daily_sync.yml (Job 1 + Job 2)
echo ══════════════════════════════════════════════════════════════
echo.

:: ─── Configuration ──────────────────────────────────────────────
set "SYNC_DIR=%~dp0💻 CODE\Phase 3 - Sync"
set VENV_DIR=%SYNC_DIR%\.venv
set PYTHON=python

:: ─── Activate venv if it exists ─────────────────────────────────
if exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [*] Activating virtual environment...
    call "%VENV_DIR%\Scripts\activate.bat"
    echo [OK] venv activated
) else (
    echo [!] No .venv found — using system Python
)
echo.

:: ─── Verify .env exists ────────────────────────────────────────
if not exist "%SYNC_DIR%\.env" (
    echo [ERROR] .env file not found in "%SYNC_DIR%"
    echo         Copy .env.example to .env and fill in your API keys.
    pause
    exit /b 1
)

:: ─── Install dependencies ──────────────────────────────────────
echo [1/14] Installing dependencies...
%PYTHON% -m pip install -r "%SYNC_DIR%\requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

:: ═══════════════════════════════════════════════════════════════
::  JOB 1: Sync → Enrich → Score → Action Ready
:: ═══════════════════════════════════════════════════════════════
echo ── JOB 1: Sync → Enrich → Score → Action Ready ────────────
echo.

echo [2/14] Running Apollo → Notion Sync (incremental, 26h window)...
%PYTHON% "%SYNC_DIR%\daily_sync.py" --mode incremental --hours 26 --gate strict
if errorlevel 1 (
    echo [ERROR] daily_sync.py failed — aborting pipeline
    pause
    exit /b 1
)
echo [OK] Sync complete
echo.

echo [3/14] Job Postings Enricher (limit 50)...
%PYTHON% "%SYNC_DIR%\job_postings_enricher.py" --limit 50
if errorlevel 1 echo [WARN] job_postings_enricher had errors (continuing)
echo.

echo [4/14] Running Lead Score...
%PYTHON% "%SYNC_DIR%\lead_score.py"
if errorlevel 1 (
    echo [ERROR] lead_score.py failed — aborting pipeline
    pause
    exit /b 1
)
echo [OK] Lead Score complete
echo.

echo [5/14] Updating Action Ready flags...
%PYTHON% "%SYNC_DIR%\action_ready_updater.py"
if errorlevel 1 (
    echo [ERROR] action_ready_updater.py failed — aborting pipeline
    pause
    exit /b 1
)
echo [OK] Action Ready updated
echo.

:: ═══════════════════════════════════════════════════════════════
::  JOB 2: Action → Sequence → Meet → Track → Brief
:: ═══════════════════════════════════════════════════════════════
echo ── JOB 2: Action → Sequence → Meet → Track → Brief ────────
echo.

echo [6/14] Running Action Engine...
%PYTHON% "%SYNC_DIR%\auto_tasks.py"
if errorlevel 1 echo [WARN] auto_tasks had errors (continuing)
echo.

echo [7/14] Auto Sequence Enrollment (limit 50)...
%PYTHON% "%SYNC_DIR%\auto_sequence.py" --limit 50
if errorlevel 1 echo [WARN] auto_sequence had errors (continuing)
echo.

echo [8/14] Meeting Tracker (7 days)...
%PYTHON% "%SYNC_DIR%\meeting_tracker.py" --days 7
if errorlevel 1 echo [WARN] meeting_tracker had errors (continuing)
echo.

echo [9/14] Meeting Analyzer (limit 10)...
%PYTHON% "%SYNC_DIR%\meeting_analyzer.py" --limit 10
if errorlevel 1 echo [WARN] meeting_analyzer had errors (continuing)
echo.

echo [10/14] Opportunity Manager...
%PYTHON% "%SYNC_DIR%\opportunity_manager.py"
if errorlevel 1 echo [WARN] opportunity_manager had errors (continuing)
echo.

echo [11/14] Analytics Tracker (7 days)...
%PYTHON% "%SYNC_DIR%\analytics_tracker.py" --days 7
if errorlevel 1 echo [WARN] analytics_tracker had errors (continuing)
echo.

echo [12/14] Outcome Tracker...
%PYTHON% "%SYNC_DIR%\outcome_tracker.py" --execute
if errorlevel 1 echo [WARN] outcome_tracker had errors (continuing)
echo.

echo [13/14] Health Check...
%PYTHON% "%SYNC_DIR%\health_check.py"
if errorlevel 1 echo [WARN] Health check flagged issues — review logs
echo.

echo [14/14] Morning Brief...
%PYTHON% "%SYNC_DIR%\morning_brief.py" --output file
if errorlevel 1 echo [WARN] morning_brief had errors (continuing)
echo.

:: ═══════════════════════════════════════════════════════════════
::  Done
:: ═══════════════════════════════════════════════════════════════
echo ══════════════════════════════════════════════════════════════
echo   Pipeline complete! Check logs in:
echo   %SYNC_DIR%\*.log
echo ══════════════════════════════════════════════════════════════
echo.
pause
