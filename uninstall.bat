@echo off
REM Uninstallation script for Windows

echo === Flexberry MarkItDown MCP Server Uninstallation ===

REM Check if virtual environment exists
if not exist ".venv" (
    echo Virtual environment not found. Nothing to uninstall.
    pause
    exit /b 0
)

REM Ask for confirmation
set /p CONFIRM="Remove virtual environment? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo Removing virtual environment...
rmdir /s /q .venv

echo.
echo Virtual environment removed.
echo.
echo To complete uninstallation:
echo 1. Remove the MCP configuration from RooCode settings
echo 2. Delete this folder: %CD%
echo 3. Optionally delete logs: %USERPROFILE%\.flexberry-markitdown-mcp
echo.

pause
