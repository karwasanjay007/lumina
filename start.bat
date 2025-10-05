@echo off
REM Multi-Agent AI Deep Researcher - Start Script
REM Run: start.bat

echo ========================================
echo Multi-Agent AI Deep Researcher
echo ========================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Load environment and start app
echo Starting application...
echo.
python run_streamlit.py

REM Alternative: Use streamlit directly
REM streamlit run app.py

pause