@echo off
setlocal
cd /d "%~dp0"
if exist "..\.venv-prototipos\Scripts\python.exe" (
    "..\.venv-prototipos\Scripts\python.exe" run_demo.py %*
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_demo.py %*
) else (
    echo No se encontro un entorno Python para la demo. Consulta README.md.
    pause
    exit /b 1
)
if errorlevel 1 pause
