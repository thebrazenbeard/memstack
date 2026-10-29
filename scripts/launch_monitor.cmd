@echo off
setlocal
set "MEMSTACK_DIR=%~dp0.."
if not exist "%MEMSTACK_DIR%\.venv\Scripts\pythonw.exe" (
  echo MemStack's local Windows virtual environment is missing.
  echo See docs\MONITOR_V01.md to create one and install BrainFlow.
  pause
  exit /b 1
)
cd /d "%MEMSTACK_DIR%"
start "MemStack Monitor" "%MEMSTACK_DIR%\.venv\Scripts\pythonw.exe" -m memstack.monitor
