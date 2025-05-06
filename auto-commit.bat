@echo off
echo Auto-Commit Script Started
echo This script will commit your changes every hour

:loop
echo.
echo Checking for changes at %time%...

REM Check if there are any changes to commit
git status --porcelain > temp_status.txt
set /p HAS_CHANGES=<temp_status.txt
del temp_status.txt

if not "%HAS_CHANGES%"=="" (
    echo Changes detected, committing...
    git add -A
    git commit -m "Auto-commit: Saving changes at %date% %time%"
    echo Committed successfully!
) else (
    echo No changes detected, nothing to commit.
)

echo Waiting for 1 hour before next check...
echo Next commit will be at approximately %time% + 1 hour
echo Press Ctrl+C to stop the auto-commit process

REM Wait for 1 hour (3600 seconds)
timeout /t 3600 /nobreak > nul

goto loop
