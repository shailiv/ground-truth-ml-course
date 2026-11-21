@echo off
rem Ground Truth: put the course online. Double-click, click Allow when the browser opens, wait a few minutes.
rem Safe to run again at any time: it re-tests, rebuilds and redeploys, and keeps the same address and passphrase.
setlocal
set "ROOT=%~dp0"
set "PATH=%ROOT%.tools\node;%PATH%"
set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%BASH%" set "BASH=bash"
echo.
echo   Ground Truth - going live
echo   -------------------------
cd /d "%ROOT%site"
call npx --yes wrangler whoami > "%TEMP%\gt-whoami.txt" 2>&1
findstr /i /c:"not authenticated" "%TEMP%\gt-whoami.txt" >nul
if not errorlevel 1 (
  echo   Step 1 of 2: your browser will open. Sign in to Cloudflare, or create a free account, and click Allow.
  echo.
  call npx --yes wrangler login
) else (
  echo   Step 1 of 2: already signed in to Cloudflare.
)
del "%TEMP%\gt-whoami.txt" >nul 2>&1
echo.
echo   Step 2 of 2: testing, building and deploying. This takes a few minutes.
echo   If Cloudflare asks you to choose a workers.dev name, type any short name: it becomes part of the address.
echo.
cd /d "%ROOT%"
"%BASH%" build/deploy.sh
set "RC=%errorlevel%"
if "%RC%"=="5" (
  echo.
  echo   The site is online but FAILED its own checks, listed above. Do not use it yet.
  echo   Ask Claude to look at this window's output before doing anything else.
  echo.
  pause
  exit /b 5
)
if not "%RC%"=="0" (
  echo.
  echo   It did not finish. The lines above say why.
  echo   Nothing is left half-open: the site only ever answers after a sign-in.
  echo.
  pause
  exit /b 1
)
call "%ROOT%show-login.cmd" open
