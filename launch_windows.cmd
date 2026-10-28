@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo AIS Biblioteka - Windows launcher
echo ========================================

where py >nul 2>&1
if errorlevel 1 (
    set "PY=python"
) else (
    set "PY=py"
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/6] Creating virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [1/6] Virtual environment already exists.
)

set "VPY=.venv\Scripts\python.exe"

echo [2/6] Installing dependencies...
"%VPY%" -m pip install --upgrade pip
if errorlevel 1 goto :error
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [3/6] Creating migrations...
"%VPY%" manage.py makemigrations library --noinput
if errorlevel 1 goto :error

echo [4/6] Applying migrations...
"%VPY%" manage.py migrate --noinput
if errorlevel 1 goto :error

echo [5/6] Loading demo data...
"%VPY%" manage.py seed_demo
if errorlevel 1 goto :error

echo [6/6] Starting server at http://127.0.0.1:8000/
start "" "http://127.0.0.1:8000/"
"%VPY%" manage.py runserver 127.0.0.1:8000
exit /b 0

:error
echo.
echo ERROR: startup failed.
echo Make sure Python 3.10+ is installed and available in PATH.
echo You can test it with: py --version
pause
exit /b 1
