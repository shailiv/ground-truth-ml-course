@echo off
rem One-time Cloudflare sign-in for deploying Ground Truth. Opens your browser; click Allow, then come back here.
rem Nothing is deployed by this file - it only stores a Wrangler login on this machine.
setlocal
set "PATH=%~dp0.tools\node;%PATH%"
cd /d "%~dp0site"
call npx --yes wrangler login
echo.
call npx --yes wrangler whoami
echo.
echo If you see your account above, you are done. You can close this window.
pause
