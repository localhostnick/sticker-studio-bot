@echo off
title Sticker Studio Telegram Bot
cd /d "%~dp0"
echo Starting Sticker Studio Telegram Bot...
python bot.py
if errorlevel 1 (
    echo.
    echo Bot stopped with an error code.
    pause
)
