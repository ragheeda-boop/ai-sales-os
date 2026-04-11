@echo off
chcp 65001 >nul 2>&1
title AI Sales OS — Muqawil Contractor Pipeline
color 0B

echo ============================================================
echo   AI Sales OS — Muqawil Contractor Pipeline (Full 6-Step)
echo ============================================================
echo.
echo   Step 1: Clean + Deduplicate scraped data
echo   Step 2: Apply priority / stage / status rules
echo   Step 3: Match against Apollo CRM (limit 500)
echo   Step 4: Check Gmail for previous outreach
echo   Step 5: Re-apply rules after Apollo/Gmail signals
echo   Step 6: Push to Notion (incremental, checkpoint-resumable)
echo.
echo ============================================================
echo.

set PYTHON=C:\Users\PC\AppData\Local\Python\bin\python.exe
set PIPELINE=%~dp0

:: ─── Verify Python exists ───────────────────────────────────────
if not exist "%PYTHON%" (
    echo [ERROR] Python not found at %PYTHON%
    echo         Update PYTHON path in this batch file.
    pause
    exit /b 1
)

:: ─── Verify pipeline script exists ──────────────────────────────
if not exist "%PIPELINE%run_muqawil_pipeline.py" (
    echo [ERROR] run_muqawil_pipeline.py not found in %PIPELINE%
    pause
    exit /b 1
)

:: ─── Run full pipeline via orchestrator ─────────────────────────
echo [*] Starting pipeline...
echo     Log: %PIPELINE%pipeline_run.log
echo.

"%PYTHON%" "%PIPELINE%run_muqawil_pipeline.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Pipeline failed. Check log: %PIPELINE%pipeline_run.log
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   DONE. Check Notion:
echo   https://notion.so/25384c7f9128462b8737773004e7d1bd
echo ============================================================
pause
