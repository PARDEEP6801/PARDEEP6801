@echo off
setlocal
title Pardeep Projects - Install / Update
rem Downloads the latest projects from GitHub into Desktop\Pardeep-Projects.
rem Your .env (API keys) and my_llms.json are never overwritten.

set "URL=https://github.com/PARDEEP6801/PARDEEP6801/archive/refs/heads/claude/pensive-newton-n2ps4m.zip"
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DESKTOP=%%D"
set "DEST=%DESKTOP%\Pardeep-Projects"
set "TMPZIP=%TEMP%\pardeep-projects.zip"
set "TMPDIR=%TEMP%\pardeep-projects"

echo.
echo  Latest project download ho raha hai...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing '%URL%' -OutFile '%TMPZIP%'; if (Test-Path '%TMPDIR%') { Remove-Item -Recurse -Force '%TMPDIR%' }; Expand-Archive -Force '%TMPZIP%' '%TMPDIR%'"
if errorlevel 1 (
  echo  Download fail hua. Internet connection check karo aur dobara chalao.
  pause
  exit /b 1
)

set "SRC="
for /d %%S in ("%TMPDIR%\*") do set "SRC=%%S\projects"
if not exist "%SRC%" (
  echo  Download mein projects folder nahi mila.
  pause
  exit /b 1
)

echo  Files copy ho rahi hain: %DEST%
robocopy "%SRC%" "%DEST%" /E /XF .env my_llms.json my_models.json /NFL /NDL /NJH /NJS /NP >nul
if %errorlevel% GEQ 8 (
  echo  Copy fail hua. Agar project chal raha hai toh use band karke dobara try karo.
  pause
  exit /b 1
)

if not exist "%DEST%\ai-studio\.env" copy "%DEST%\ai-studio\.env.example" "%DEST%\ai-studio\.env" >nul
rmdir /s /q "%TMPDIR%" 2>nul
del "%TMPZIP%" 2>nul

echo.
echo  Ho gaya! Project yahan hai: %DEST%
echo  (Aage update ke liye isi folder ki Update-Projects.bat pe double-click karna.)
echo.
start "" "%DEST%"
pause
