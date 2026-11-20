@echo off
rem Double-click this file to start the AI Research Assistant.
rem It uses the Python inside .venv, so there's no need to activate anything first.

cd /d "%~dp0"
".venv\Scripts\python.exe" -m streamlit run app.py
pause
