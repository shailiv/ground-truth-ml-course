@echo off
rem Ground Truth on this computer only, for a look before (or without) going live. Passphrase: test
setlocal
set "ROOT=%~dp0"
set "PATH=%ROOT%.tools\node;%PATH%"
cd /d "%ROOT%"
echo.
echo   Opening http://localhost:8788   (passphrase: test)
echo   Close this window to stop it.
echo.
start "" http://localhost:8788
node build/dev_server.mjs 8788
pause
