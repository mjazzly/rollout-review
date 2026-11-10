@echo off
rem get.cmd: bring the PC up to date with the Mac, then open the report.
rem   Stops if Power BI Desktop is open. Throws away any unsaved-to-git changes under report\
rem   (the Mac's files are the source), pulls, and opens report\Rollout review.pbip.
title Rollout review: get
set CLOSE_HINT=Close it, no need to save, then run get.cmd again.
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

echo Throwing away local changes under report\ ...
git checkout -q -- report/
if errorlevel 1 goto gitfail
git clean -fdq -- report/
if errorlevel 1 goto gitfail

set OTHER=
for /f "delims=" %%l in ('git status --porcelain') do set OTHER=1
if defined OTHER (
  echo STOPPED: there are changes outside report\ that get.cmd will not touch:
  git --no-pager status --short
  echo Nothing was pulled or opened.
  goto fail
)

echo Pulling from GitHub ...
git pull --ff-only -q
if errorlevel 1 (
  echo STOPPED: the pull did not go through. Nothing was opened.
  goto fail
)
for /f "delims=" %%c in ('git log -1 --oneline') do set LAST=%%c
echo.
echo DONE: up to date at %LAST%
echo Opening the report ...
start "" "%~dp0report\Rollout review.pbip"
timeout /t 5 >nul
exit /b 0

:gitfail
echo STOPPED: git could not throw away the local changes under report\. Nothing was pulled.
:fail
echo.
pause
exit /b 1
