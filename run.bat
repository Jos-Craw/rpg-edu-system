@echo off
chcp 65001 >nul
title Запуск Журнала
cd /d "%~dp0"

:: 1. Проверка наличия venv
if not exist "venv" (
    echo [!] Окружение не найдено. Создаю...
    python -m venv venv
)

:: 2. Активация
call venv\Scripts\activate

:: 3. Обновление библиотек (быстрая проверка)
echo [1/3] Проверка зависимостей...
pip install -q django plotly psycopg2-binary

:: 4. Миграции
echo [2/3] Синхронизация базы данных...
python manage.py migrate

:: 5. Запуск
echo [3/3] Сервер запускается на http://127.0.0.1:8000
start http://127.0.0.1:8000
python manage.py runserver

pause