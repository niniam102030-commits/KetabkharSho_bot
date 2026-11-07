@echo off
chcp 65001 >nul
title KetabKharsho Bot Runner

echo ======================================================
echo    KetabKharsho Bot - Starter Script
echo ======================================================
echo.

cd /d "%~dp0"

echo [1/3] Dar hale barresi mohite majazi (venv)...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [+] Mohite majazi .venv peyda shod va faal shod.
) else (
    set "PYTHON_EXE=python"
    echo [!] Mohite majazi .venv yaft nashod. Az python pishfarze system estefadeh mishavad.
)

echo.
echo [2/3] Dar hale barresi file .env va niazmandiha...
if not exist ".env" (
    echo [WARNING] File .env vojood nadarad! Lotfan ghabl az ejra .env ra tanzim konid.
)

echo.
echo [3/3] Dar hale ejraye robat (main.py)...
echo ======================================================
echo [INFO] Robat ba movafaghiat start shod.
echo [INFO] Baraye tavaghofe robat Dokmeye Ctrl + C ra feshar dahid.
echo ======================================================
echo.

"%PYTHON_EXE%" main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================
    echo [ERROR] Robat ba khata motavaghef shod (Error code: %ERRORLEVEL%)!
    echo ======================================================
) else (
    echo.
    echo ======================================================
    echo [INFO] Robat ba movafaghiat baste shod.
    echo ======================================================
)

echo.
pause
