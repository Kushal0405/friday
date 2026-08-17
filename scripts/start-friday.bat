@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Starting FRIDAY
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
    echo [FAIL] Python not found on PATH.
    echo [FAIL] Python not found on PATH.
    exit /b 1
)
echo [ OK ] Python found

where node >nul 2>nul
if errorlevel 1 (
    echo [FAIL] Node.js not found on PATH.
    exit /b 1
)
echo [ OK ] Node found

set ROOT=%~dp0..
set BACKEND=%ROOT%\backend
set FRONTEND=%ROOT%\frontend

if not exist "%BACKEND%\venv\Scripts\python.exe" (
    echo [FAIL] Backend virtual environment not found at %BACKEND%\venv
    echo        Run: python -m venv backend\venv ; backend\venv\Scripts\pip install -r backend\requirements.txt
    exit /b 1
)

echo Starting backend...
start "FRIDAY Backend" /D "%BACKEND%" "%BACKEND%\venv\Scripts\python.exe" -m app.main

echo Waiting for backend health check...
set HEALTHY=0
for /l %%i in (1,1,30) do (
    curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8765/health > "%TEMP%\friday_health.txt" 2>nul
    set /p CODE=<"%TEMP%\friday_health.txt"
    if "!CODE!"=="200" (
        set HEALTHY=1
        goto :backend_ready
    )
    timeout /t 1 /nobreak >nul
)

:backend_ready
if "%HEALTHY%"=="0" (
    echo [FAIL] Backend did not become healthy in time.
    exit /b 1
)
echo [ OK ] Backend healthy

echo Starting FRIDAY HUD...
pushd "%FRONTEND%"
call npm run dev
popd

echo FRIDAY closed. Stopping backend...
taskkill /FI "WINDOWTITLE eq FRIDAY Backend*" /T /F >nul 2>nul

endlocal
