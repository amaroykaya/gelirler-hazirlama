@echo off
cd /d %~dp0

if not exist ".venv\Scripts\activate.bat" (
    echo HATA: .venv bulunamadi. Lutfen once sanal ortami olusturun.
    pause
    exit /b 1
)

call .venv\Scripts\activate

python gelirhazirlama.py

pause
