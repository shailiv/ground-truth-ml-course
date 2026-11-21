@echo off
rem Ground Truth: connect the in-page tutor. While this window is open, questions asked in a lesson are answered
rem on the page by Claude Code on this computer (your own Claude subscription). Close the window to disconnect;
rem the lesson page then offers "Open in Claude" instead.
setlocal
set "ROOT=%~dp0"
if not exist "%ROOT%.secrets\relay.json" (
  echo   The site is not online yet. Run go-live.cmd first.
  pause
  exit /b 1
)
title Ground Truth tutor - leave this window open
echo.
echo   The tutor is connected while this window stays open.
echo.
python "%ROOT%relay\tutor_relay.py" --config "%ROOT%.secrets\relay.json"
echo.
pause
