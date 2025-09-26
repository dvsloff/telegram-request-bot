# Telegram Request Bot

Простой Telegram-бот-визитка на Python.  
Бот запускается локально и отвечает в чате.

##  Запуск проекта

1. Клонируй репозиторий:
   ```bash
   git clone https://github.com/dvsloff/telegram-request-bot.git
   cd telegram-request-bot
   
2. Создай виртуальное окружение:
    ```bash
    python -m venv venv
   
3. Активируй виртуальное окружение:

    ```bash
    venv\Scripts\activate

4. Установи зависимости:

    ```bash
    pip install -r requirements.txt
   
5. Запусти бота:

    ```bash
    python bot-vizitka.py
   
Заметки

Перед запуском укажи свой TELEGRAM_BOT_TOKEN в коде или через переменные окружения.

Для работы нужен установленный Python 3.10+.

Зависимости

aiogram
 — работа с Telegram Bot API

openpyxl
 — работа с Excel-файлами

Автор: Danila Veselov (@dvsloff)