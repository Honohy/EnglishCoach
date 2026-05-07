@echo off
title EnglishCoach - Deploy to VPS

:: ============================================================
::  SETTINGS - fill in before first run
:: ============================================================
set VPS_HOST=185.244.181.124
set VPS_USER=root
set VPS_PASS=hq8:k8Z==T1QW:uGD5Eb
set REPO_URL=https://github.com/Honohy/EnglishCoach.git
set REPO_DIR=/root/EnglishCoach
:: ============================================================

echo.
echo === EnglishCoach - Deploy to VPS ===
echo.

:: Check for plink (PuTTY)
where plink >nul 2>&1
if errorlevel 1 (
    if exist "C:\Program Files\PuTTY\plink.exe" (
        set PLINK="C:\Program Files\PuTTY\plink.exe"
    ) else if exist "C:\Program Files (x86)\PuTTY\plink.exe" (
        set PLINK="C:\Program Files (x86)\PuTTY\plink.exe"
    ) else (
        echo [ERROR] plink not found.
        echo Install PuTTY: https://www.putty.org/
        pause
        exit /b 1
    )
) else (
    set PLINK=plink
)

:: Step 1 - Push to GitHub
echo [1/3] Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo [ERROR] git push failed. Check: git status
    pause
    exit /b 1
)
echo        Done.
echo.

:: Step 2 - Accept host key automatically (first time)
echo [2/3] Connecting to VPS %VPS_HOST%...
echo y | %PLINK% -pw %VPS_PASS% %VPS_USER%@%VPS_HOST% "echo connected" >nul 2>&1

:: Step 3 - Deploy on VPS
echo [3/3] Deploying on VPS...
echo.

%PLINK% -pw %VPS_PASS% %VPS_USER%@%VPS_HOST% "if systemctl list-unit-files englishcoach.service --no-legend | grep -q englishcoach; then cd %REPO_DIR% && bash deploy.sh; elif [ -d '%REPO_DIR%' ]; then cd %REPO_DIR% && bash setup.sh; else git clone %REPO_URL% %REPO_DIR% && cd %REPO_DIR% && bash setup.sh; fi"

if errorlevel 1 (
    echo.
    echo [ERROR] Something went wrong on VPS.
    echo Connect manually: ssh %VPS_USER%@%VPS_HOST%
) else (
    echo.
    echo === Deploy finished! ===
    echo Logs: ssh %VPS_USER%@%VPS_HOST% then: journalctl -u englishcoach -f
)

echo.
pause
