@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_demo.py %*
) else if exist "..\.venv-prototipos\Scripts\python.exe" (
    "..\.venv-prototipos\Scripts\python.exe" run_demo.py %*
) else (
    py -3.13 run_demo.py %*
)
if errorlevel 1 pause
