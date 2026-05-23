@echo off
echo ============================================
echo  Instalando dependencias (puede tardar...)
echo ============================================
python -m pip install --upgrade pip --quiet
python -m pip install flask pywebview
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Fallo la instalacion de dependencias.
    echo Asegurate de tener Python instalado y en el PATH.
    pause
    exit /b 1
)
echo.
echo ============================================
echo  Iniciando Compilador...
echo ============================================
python app.py
pause
