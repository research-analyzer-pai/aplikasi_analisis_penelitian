@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   RESEARCH ANALYZER PROFESSIONAL v5.0
echo ================================================
where py >nul 2>nul
if %errorlevel%==0 (
  py -m venv .venv 2>nul
  call .venv\Scripts\activate.bat
) else (
  where python >nul 2>nul || (echo Python belum terpasang. Instal Python 3.10 atau lebih baru. & pause & exit /b 1)
  python -m venv .venv 2>nul
  call .venv\Scripts\activate.bat
)
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (echo Gagal memasang dependensi. Periksa koneksi internet dan versi Python. & pause & exit /b 1)
streamlit run app.py
pause
