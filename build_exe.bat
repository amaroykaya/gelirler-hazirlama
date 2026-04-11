@echo off
echo ========================================
echo Gelir Hazirlama EXE Olusturma
echo ========================================
echo.

REM Python'u bul
set PYTHON_CMD=
where py >nul 2>&1
if %ERRORLEVEL% == 0 (
    set PYTHON_CMD=py
    echo Python bulundu: py
    goto :found_python
)

where python >nul 2>&1
if %ERRORLEVEL% == 0 (
    set PYTHON_CMD=python
    echo Python bulundu: python
    goto :found_python
)

where python3 >nul 2>&1
if %ERRORLEVEL% == 0 (
    set PYTHON_CMD=python3
    echo Python bulundu: python3
    goto :found_python
)

REM Yaygın Python yollarını kontrol et
if exist "C:\Python314\python.exe" (
    set PYTHON_CMD=C:\Python314\python.exe
    echo Python bulundu: C:\Python314\python.exe
    goto :found_python
)

if exist "C:\Python313\python.exe" (
    set PYTHON_CMD=C:\Python313\python.exe
    echo Python bulundu: C:\Python313\python.exe
    goto :found_python
)

if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    echo Python bulundu: C:\Python312\python.exe
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python314\python.exe
    echo Python bulundu: %PYTHON_CMD%
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
    echo Python bulundu: %PYTHON_CMD%
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    echo Python bulundu: %PYTHON_CMD%
    goto :found_python
)

echo HATA: Python bulunamadi!
echo Lutfen Python'in kurulu oldugundan ve PATH'te oldugundan emin olun.
echo.
echo Python kurulumu icin PYTHON_KURULUMU.md dosyasina bakin.
pause
exit /b 1

:found_python
echo.
echo Python versiyonu:
%PYTHON_CMD% --version
echo.

REM pip'i kontrol et
echo pip kontrol ediliyor...
%PYTHON_CMD% -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo HATA: pip bulunamadi!
    pause
    exit /b 1
)
echo pip bulundu.
echo.

REM Paketleri kur
echo ========================================
echo Paketler kuruluyor...
echo ========================================
echo.

echo [1/6] pandas kuruluyor...
%PYTHON_CMD% -m pip install pandas>=1.5.0
if %ERRORLEVEL% neq 0 (
    echo HATA: pandas kurulamadi!
    pause
    exit /b 1
)

echo [2/6] openpyxl kuruluyor...
%PYTHON_CMD% -m pip install openpyxl>=3.0.0
if %ERRORLEVEL% neq 0 (
    echo HATA: openpyxl kurulamadi!
    pause
    exit /b 1
)

echo [3/6] numpy kuruluyor...
%PYTHON_CMD% -m pip install numpy>=1.20.0
if %ERRORLEVEL% neq 0 (
    echo HATA: numpy kurulamadi!
    pause
    exit /b 1
)

echo [4/6] requests kuruluyor...
%PYTHON_CMD% -m pip install requests>=2.28.0
if %ERRORLEVEL% neq 0 (
    echo HATA: requests kurulamadi!
    pause
    exit /b 1
)

echo [5/6] pdfplumber kuruluyor...
%PYTHON_CMD% -m pip install pdfplumber>=0.10.0
if %ERRORLEVEL% neq 0 (
    echo HATA: pdfplumber kurulamadi!
    pause
    exit /b 1
)

echo [6/6] pyinstaller kuruluyor...
%PYTHON_CMD% -m pip install pyinstaller>=5.0.0
if %ERRORLEVEL% neq 0 (
    echo HATA: pyinstaller kurulamadi!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Tum paketler basariyla kuruldu!
echo ========================================
echo.

REM PyInstaller ile EXE olustur
echo ========================================
echo EXE dosyasi olusturuluyor...
echo ========================================
echo.

%PYTHON_CMD% -m PyInstaller --onefile --windowed --name=GelirHazirlama --hidden-import=requests --hidden-import=pdfplumber gelirhazirlama.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo HATA: EXE olusturulamadi!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Basarili! EXE dosyasi dist klasorunde.
echo ========================================
echo.
echo EXE dosyasi: dist\GelirHazirlama.exe
echo.
pause

