@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m streamlit run "web\app.py"
echo.
echo Dashboard is closed or you stopped it.
pause
