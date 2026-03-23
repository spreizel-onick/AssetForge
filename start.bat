@echo off
title AssetForge
echo.
echo  ===================================
echo    AssetForge
echo    http://localhost:5000
echo  ===================================
echo.
cd /d "%~dp0"
start "" http://localhost:5000
python app.py
pause
