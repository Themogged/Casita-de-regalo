@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo No se encontro el entorno virtual .venv
    echo Instala dependencias con:
    echo py -3.13 -m venv .venv
    echo .venv\Scripts\python -m pip install -r requirements.txt
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python manage.py runserver
