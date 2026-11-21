@echo off
rem Ground Truth: show the address and the passphrase, and put the passphrase on the clipboard.
setlocal
set "ROOT=%~dp0"
if not exist "%ROOT%.secrets\url.txt" (
  echo   The site is not online yet. Run go-live.cmd first.
  pause
  exit /b 1
)
set /p URL=<"%ROOT%.secrets\url.txt"
set /p PASS=<"%ROOT%.secrets\passphrase.txt"
echo.
echo   Your course:   %URL%
echo   Passphrase:    %PASS%
echo.
<nul set /p "=%PASS%" | clip
echo   The passphrase is on your clipboard: paste it into the sign-in box.
echo   On your phone: open the same address and type the passphrase once. It stays signed in for 60 days.
echo   For answers inside the lesson page, start tutor-relay.cmd and leave its window open.
echo.
if /i "%~1"=="open" start "" "%URL%"
pause
