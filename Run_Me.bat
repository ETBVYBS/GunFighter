@echo off
echo Setting up the Game..
:: Checking to see if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python to run the game.
    echo Please install python from https://www.python.org and click add check "Add Python to PATH" during installation.
    pause
    exit
)
echo Python is installed. Downloading dependencies...
(Pygame)....
python -m pip install pygame

Echo All dependencies are installed. Starting the game...
python gun_fighter.py
pause