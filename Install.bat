@echo off
echo Installing all required packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo Installation complete!
echo Run: start.bat
pause