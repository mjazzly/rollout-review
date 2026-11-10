@echo off
rem send.cmd: send what you saved in Power BI Desktop (changes under report\) to GitHub.
rem   Stops if Power BI Desktop is open or anything outside report\ has changed. Asks for a
rem   message, commits report\, pulls (rebasing on the Mac's latest), pushes, and says whether
rem   it worked.
title Rollout review: send
set CLOSE_HINT=Save in it, close it, then run send.cmd again.
setlocal
rem git never opens its pager here: a long list would wait at a ":" (round 11)
set GIT_PAGER=cat
set PAGER=cat
cd /d "%~dp0"

where git >nul 2>&1
if errorlevel 1 (
  echo STOPPED: git is not installed, or not on the PATH. Nothing was changed.
  goto fail
)
tasklist /FI "IMAGENAME eq PBIDesktop.exe" 2>nul | find /I "PBIDesktop.exe" >nul
if not errorlevel 1 (
  echo STOPPED: Power BI Desktop is open. %CLOSE_HINT%
  goto fail
)
set BRANCH=
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%b
if not "%BRANCH%"=="main" (
  echo STOPPED: this copy is on branch "%BRANCH%", not main. Nothing was changed.
  goto fail
)

git diff --quiet HEAD -- . ":!report"
if errorlevel 1 goto outside
set OUTSIDE=
for /f "delims=" %%l in ('git ls-files --others --exclude-standard -- . ":!report"') do set OUTSIDE=1
if defined OUTSIDE goto outside

git add -A -- report
if errorlevel 1 (
  echo STOPPED: git could not add the changes under report\. Nothing was sent.
  goto fail
)
git diff --cached --quiet
if not errorlevel 1 goto nothing_new

echo Changed under report\:
git --no-pager diff --cached --stat
echo.
set MSG=
set /p MSG=Type a message for this save, then press Enter: 
if not defined MSG (
  echo STOPPED: no message typed. The changes are staged but not committed or sent.
  goto fail
)
set MSG=%MSG:"='%
git commit -q -m "%MSG%"
if errorlevel 1 (
  echo STOPPED: the commit did not go through. Nothing was sent.
  goto fail
)
goto pull

:nothing_new
set AHEAD=0
for /f "delims=" %%n in ('git rev-list --count @{u}..HEAD') do set AHEAD=%%n
if "%AHEAD%"=="0" (
  echo NOTHING TO SEND: no changes under report\ since the last send.
  goto fail
)
echo No new changes, but %AHEAD% earlier save^(s^) not sent yet. Sending those.

:pull
echo Pulling the Mac's latest from GitHub ...
git pull --rebase -q
if errorlevel 1 (
  git rebase --abort >nul 2>&1
  echo.
  echo FAILED: your save and a newer change from the Mac touch the same files.
  echo Your save is kept on this PC as a commit; nothing was sent. Tell Claude.
  goto fail
)
echo Pushing ...
git push -q
if errorlevel 1 (
  echo.
  echo FAILED: the push did not go through. Your save is kept on this PC as a commit.
  echo Check the internet connection and run send.cmd again.
  goto fail
)
for /f "delims=" %%c in ('git log -1 --oneline') do set LAST=%%c
echo.
echo SENT: GitHub now has %LAST%
echo.
pause
exit /b 0

:outside
echo STOPPED: there are changes outside report\, which send.cmd does not send:
git --no-pager status --short -- . ":!report"
echo Nothing was committed or sent. Tell Claude.
:fail
echo.
pause
exit /b 1
