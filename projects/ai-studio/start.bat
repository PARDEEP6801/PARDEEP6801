@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py server.py & goto :end)
where python >nul 2>nul && (python server.py & goto :end)
echo Python nahi mila. https://www.python.org/downloads/ se install karo ("Add Python to PATH" tick karna).
:end
pause
