@echo off

title Sistema de Lanchonete - Inicializador
echo Aguarde... O sistema esta sendo preparado.

python -m pip install --upgrade pip -q >nul 2>&1
python -m pip install customtkinter reportlab -q >nul 2>&1

start "" /b python lanchonete.py

exit