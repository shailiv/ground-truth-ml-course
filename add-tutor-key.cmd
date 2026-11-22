@echo off
rem Ground Truth: give the tutor its own Claude API key, so answers appear in the lesson page with no relay and no
rem computer of yours running. Paid from the API credit included in a Claude Max plan.
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"
echo.
echo   Ground Truth - a Claude API key for the tutor
echo   ---------------------------------------------
echo   This uses the API credit that comes with your Claude Max plan: 100 dollars a month, refilled
echo   with each plan payment. No card is needed. With no card on file nothing can be charged:
echo   when the month's credit is used up, the tutor simply stops until it refills.
echo.
echo   Two pages will open in your browser. Do these two things, then come back to this window:
echo.
echo     1. claude.ai - Settings - Billing: under "API credits", choose the Console organization
echo        that should receive the credits and link it. This is done once.
echo     2. Claude Console - API keys: create a key, name it ground-truth-tutor, choose the
echo        workspace "Default" for it (not "All workspaces"), and copy it.
echo.
echo   Do NOT add a payment method and do NOT turn on auto-reload in the Console.
echo.
pause
start "" "https://claude.ai/settings/billing"
start "" "https://platform.claude.com/settings/keys"
echo.
python build\set_tutor_key.py
if errorlevel 1 (
  echo.
  pause
  exit /b 1
)
echo.
echo   Publishing the site with the key...
call "%ROOT%go-live.cmd"
