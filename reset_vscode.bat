@echo off
echo Closing VS Code...
taskkill /f /im code.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Resetting VS Code window layout...
if exist "%APPDATA%\Code\User\workspaceStorage" (
    echo Backing up workspaceStorage to workspaceStorage_backup
    xcopy /E /I /Y "%APPDATA%\Code\User\workspaceStorage" "%APPDATA%\Code\User\workspaceStorage_backup" >nul
    echo Removing workspaceStorage folder
    rmdir /S /Q "%APPDATA%\Code\User\workspaceStorage"
)

echo Starting VS Code with clean layout...
start "" "code" "%CD%"

echo Done! VS Code should now have a clean layout.
echo If you need to restore your previous settings, check the backup at:
echo %APPDATA%\Code\User\workspaceStorage_backup
