@echo off
REM Kurulum scripti (Windows)

echo AI Egitim Dokumani Hazirlama - Kurulum
echo ==========================================
echo.

REM Virtual environment olustur
if not exist "venv" (
    echo Virtual environment olusturuluyor...
    python -m venv venv
    echo Virtual environment olusturuldu
) else (
    echo Virtual environment zaten mevcut
)

echo.
echo Paketler yukleniyor...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Dizinler olusturuluyor...
if not exist "data\output" mkdir data\output
if not exist "data\checkpoints" mkdir data\checkpoints
if not exist "data\logs" mkdir data\logs
if not exist "data\images" mkdir data\images
if not exist "data\vector_db" mkdir data\vector_db
if not exist "data\uploads" mkdir data\uploads

echo.
echo Kurulum tamamlandi!
echo.
echo Kullanim icin:
echo   venv\Scripts\activate
echo   python cli\main.py --input dokuman.pdf
echo.
pause
