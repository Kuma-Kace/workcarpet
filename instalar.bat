@echo off
chcp 65001 > NUL
title Instalador y Compilador - Convertidor de PDF a AudioTexto y Audiolibro

echo =======================================================================
echo     Instalador del Convertidor de PDF a AudioTexto / Audiolibro MP3
echo =======================================================================
echo.

:: Verificar si Python está instalado
python --version >NUL 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no se encuentra en el PATH del sistema.
    echo Por favor instala Python 3.10 o superior desde https://www.python.org/ y vuelve a intentarlo.
    echo Asegúrate de marcar la casilla "Add Python to PATH" durante la instalación.
    echo.
    pause
    exit /b 1
)

echo [1/3] Instalando y actualizando dependencias de Python...
python -m pip install --upgrade pip
python -m pip install pypdf edge-tts pyinstaller reportlab

echo.
echo [2/3] Compilando la aplicación ejecutable (.exe)...
python build_installer.py

echo.
echo =======================================================================
if exist "dist\Convertidor_AudioLibro_TextAloud.exe" (
    echo   ¡INSTALACIÓN Y COMPILACIÓN COMPLETADA CON ÉXITO!
    echo   El archivo ejecutable listo para usar se generó en:
    echo   %CD%\dist\Convertidor_AudioLibro_TextAloud.exe
) else (
    echo   Se completó el proceso. Revisa la carpeta dist\
)
echo =======================================================================
echo.
pause
