@echo off
cd /d "%~dp0"
echo Installing... please wait
python -m pip install -r requirements.txt
echo.
echo Starting site... DO NOT close this window
start "" http://127.0.0.1:5000
python app.py
pause
