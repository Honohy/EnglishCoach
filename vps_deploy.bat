@echo off
chcp 65001 > nul
title EnglishCoach — Deploy to VPS

:: ============================================================
::  НАСТРОЙКИ — заполните перед первым запуском
:: ============================================================
set VPS_HOST=YOUR_VPS_IP
set VPS_USER=root
set VPS_PASS=YOUR_VPS_PASSWORD
set REPO_URL=https://github.com/YOUR_USERNAME/YOUR_REPO.git
set REPO_DIR=/root/EnglishCoach
:: ============================================================

echo.
echo === EnglishCoach — Deploy to VPS ===
echo.

:: Проверяем наличие plink (PuTTY)
where plink >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files\PuTTY\plink.exe" (
        set PLINK="C:\Program Files\PuTTY\plink.exe"
    ) else if exist "C:\Program Files (x86)\PuTTY\plink.exe" (
        set PLINK="C:\Program Files (x86)\PuTTY\plink.exe"
    ) else (
        echo [ERROR] plink не найден.
        echo Установите PuTTY: https://www.putty.org/
        echo После установки перезапустите батник.
        pause
        exit /b 1
    )
) else (
    set PLINK=plink
)

:: Шаг 1 — Пушим на GitHub
echo [1/3] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo [ERROR] git push завершился с ошибкой.
    echo Проверьте, что все изменения закоммичены: git status
    pause
    exit /b 1
)
echo        Done.
echo.

:: Шаг 2 — Принимаем ключ хоста автоматически (первый раз)
echo [2/3] Connecting to VPS %VPS_HOST%...
echo y | %PLINK% -pw %VPS_PASS% %VPS_USER%@%VPS_HOST% "echo connected" >nul 2>&1

:: Шаг 3 — Деплой на VPS
echo [3/3] Deploying on VPS...
echo.

%PLINK% -pw %VPS_PASS% %VPS_USER%@%VPS_HOST% ^
    "if [ -d '%REPO_DIR%' ]; then cd %REPO_DIR% && bash deploy.sh; else git clone %REPO_URL% %REPO_DIR% && cd %REPO_DIR% && bash setup.sh; fi"

if errorlevel 1 (
    echo.
    echo [ERROR] Что-то пошло не так на VPS.
    echo Подключитесь вручную: ssh %VPS_USER%@%VPS_HOST%
) else (
    echo.
    echo === Deploy finished! ===
    echo Logs: ssh %VPS_USER%@%VPS_HOST% "journalctl -u englishcoach -f"
)

echo.
pause
