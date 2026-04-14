@echo off
REM Installation script for Windows

echo === Flexberry MarkItDown MCP Server Installation ===

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is required but not installed.
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python: %PYTHON_VERSION%

REM Create virtual environment
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -e .

REM Prepare paths with escaped backslashes for JSON
set "JSON_PATH=%CD:\=\\%"

echo.
echo === Installation complete! ===
echo.
echo To configure RooCode, add this to your mcp_settings.json:
echo.
echo {
echo   "mcpServers": {
echo     "flexberry-markitdown": {
echo       "command": "%JSON_PATH%\\.venv\\Scripts\\python.exe",
echo       "args": ["-m", "flexberry_markitdown_mcp.server"],
echo       "cwd": "%JSON_PATH%"
echo     }
echo   }
echo }
echo.
echo Repository: https://github.com/Flexberry/flexberry-markitdown-mcp
echo.

pause
