@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo Starting FARE MATRIX Dashboard...
echo Open your browser at: http://localhost:8501
streamlit run dashboard.py
