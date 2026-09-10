@echo off
rem One-click CV publish: double-click to publish the newest CV from the
rem job-materials folder, or drop a CV .docx onto this file to publish that one.
setlocal
cd /d "%~dp0"
echo Publishing the latest CV to davidawoyemi.net ...
echo.
python "scripts\sync_cv.py" %*
echo.
pause
