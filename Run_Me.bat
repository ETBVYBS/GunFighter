@echo off
echo Checking for Python...
:: Try the Python Launcher first (works even if PATH was unchecked)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :START_GAME
)

:: Try standard python command
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :START_GAME
)

echo.
echo ERROR: Python not found! 
echo Please install it from python.org and check "Add to PATH".
pause
exit

:START_GAME
echo Installing Game Engine (Pygame)...
%PY_CMD% -m pip install pygame
echo Starting Gun Fighter...
%PY_CMD% gun_fighter.py
pause
