@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ╔══════════════════════════════════════════════╗
echo ║       English Practice Bot — Installer       ║
echo ╚══════════════════════════════════════════════╝
echo.

:: ─── Проверка прав администратора ───────────────────────────────────────────
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ОШИБКА] Запусти батник от имени Администратора!
    echo   Правая кнопка на файле → "Запуск от имени администратора"
    pause
    exit /b 1
)

:: ─── Переходим в папку батника (корень проекта) ──────────────────────────────
cd /d "%~dp0"
echo [INFO] Рабочая папка: %CD%
echo.

:: ══════════════════════════════════════════════════════════════════════════════
:: ШАГ 1 — Python
:: ══════════════════════════════════════════════════════════════════════════════
echo [1/5] Проверка Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo       Python не найден. Скачиваю установщик...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
    if %errorLevel% neq 0 (
        echo [ОШИБКА] Не удалось скачать Python. Проверь интернет.
        pause & exit /b 1
    )
    echo       Устанавливаю Python 3.11 (тихая установка)...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del python_installer.exe

    :: Обновляем PATH для текущей сессии
    for /f "tokens=*" %%i in ('where python 2^>nul') do set PYTHON_PATH=%%i
    if "!PYTHON_PATH!"=="" (
        echo [ОШИБКА] Python установлен, но не найден в PATH.
        echo   Перезапусти батник или добавь Python в PATH вручную.
        pause & exit /b 1
    )
    echo       Python установлен: !PYTHON_PATH!
) else (
    for /f "tokens=*" %%v in ('python --version') do echo       Найден: %%v
)

:: ══════════════════════════════════════════════════════════════════════════════
:: ШАГ 2 — pip актуален
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo [2/5] Обновление pip...
python -m pip install --upgrade pip --quiet
echo       pip обновлён.

:: ══════════════════════════════════════════════════════════════════════════════
:: ШАГ 3 — ffmpeg
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo [3/5] Проверка ffmpeg...
ffmpeg -version >nul 2>&1
if %errorLevel% neq 0 (
    echo       ffmpeg не найден. Скачиваю...

    :: Скачиваем через curl (есть в Windows 10+)
    curl -L -o ffmpeg.zip https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip
    if %errorLevel% neq 0 (
        echo [ОШИБКА] Не удалось скачать ffmpeg. Проверь интернет.
        pause & exit /b 1
    )

    echo       Распаковываю ffmpeg...
    :: Используем PowerShell для распаковки
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_tmp' -Force"
    
    :: Находим папку с bin внутри архива и копируем
    if not exist "C:\ffmpeg" mkdir "C:\ffmpeg"
    for /d %%D in (ffmpeg_tmp\ffmpeg-*) do (
        xcopy "%%D\bin\*" "C:\ffmpeg\bin\" /E /I /Y >nul
    )

    :: Убираем временные файлы
    del ffmpeg.zip
    rmdir /s /q ffmpeg_tmp

    :: Добавляем в системный PATH
    powershell -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path','Machine') + ';C:\ffmpeg\bin', 'Machine')"
    set PATH=%PATH%;C:\ffmpeg\bin

    ffmpeg -version >nul 2>&1
    if %errorLevel% neq 0 (
        echo [ПРЕДУПРЕЖДЕНИЕ] ffmpeg установлен в C:\ffmpeg\bin, но недоступен в этой сессии.
        echo   После перезапуска терминала всё будет работать.
    ) else (
        echo       ffmpeg установлен успешно.
    )
) else (
    echo       ffmpeg уже установлен.
)

:: ══════════════════════════════════════════════════════════════════════════════
:: ШАГ 4 — Зависимости Python
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo [4/5] Установка Python-зависимостей...
if not exist "english_bot\requirements.txt" (
    echo [ОШИБКА] Файл english_bot\requirements.txt не найден!
    echo   Убедись, что батник лежит в корне проекта рядом с папкой english_bot\
    pause & exit /b 1
)
python -m pip install -r english_bot\requirements.txt
if %errorLevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости. Проверь requirements.txt
    pause & exit /b 1
)
echo       Все зависимости установлены.

:: ══════════════════════════════════════════════════════════════════════════════
:: ШАГ 5 — .env файл
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo [5/5] Настройка .env...
if exist "english_bot\.env" (
    echo       Файл .env уже существует, пропускаю.
) else (
    echo       Создаю .env из шаблона...
    copy "english_bot\.env.example" "english_bot\.env" >nul

    echo.
    echo  ┌─────────────────────────────────────────────────┐
    echo  │  Заполни API-ключи в файле english_bot\.env     │
    echo  │                                                  │
    echo  │  BOT_TOKEN       — от @BotFather в Telegram     │
    echo  │  ANTHROPIC_API_KEY — console.anthropic.com      │
    echo  │  OPENAI_API_KEY  — platform.openai.com          │
    echo  └─────────────────────────────────────────────────┘
    echo.
    echo  Открываю .env в Блокноте. Заполни и сохрани файл.
    notepad "english_bot\.env"
    echo.
    echo  Нажми любую клавишу когда заполнишь .env...
    pause >nul
)

:: ─── Финальная проверка .env ─────────────────────────────────────────────────
findstr /C:"BOT_TOKEN=your" "english_bot\.env" >nul 2>&1
if %errorLevel% equ 0 (
    echo.
    echo [ПРЕДУПРЕЖДЕНИЕ] В .env остались placeholder-значения!
    echo   Отредактируй english_bot\.env и замени все your_*_here на реальные ключи.
    echo   Потом запусти start_bot.bat
    pause
    exit /b 0
)

:: ══════════════════════════════════════════════════════════════════════════════
:: Создаём start_bot.bat для удобного запуска
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo [INFO] Создаю start_bot.bat для запуска бота...
(
    echo @echo off
    echo chcp 65001 ^>nul
    echo cd /d "%%~dp0english_bot"
    echo echo Запускаю English Practice Bot...
    echo python bot.py
    echo pause
) > start_bot.bat
echo       Готово.

:: ══════════════════════════════════════════════════════════════════════════════
:: ИТОГ
:: ══════════════════════════════════════════════════════════════════════════════
echo.
echo ╔══════════════════════════════════════════════╗
echo ║           Установка завершена! ✓             ║
echo ╠══════════════════════════════════════════════╣
echo ║  Для запуска бота используй:                 ║
echo ║       start_bot.bat                          ║
echo ╚══════════════════════════════════════════════╝
echo.
pause
