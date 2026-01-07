import os
import sys

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

import telebot
from dotenv import load_dotenv, dotenv_values
import subprocess  # Для запуска core_engine.py

# Загружаем переменные из .env
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path)

# Загружаем все ключи для передачи в subprocess
env_vars = dotenv_values(env_path)

# Инициализация бота
token = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 Singularity v1.0 на связи. Я готов запустить Рой по твоему приказу. Просто напиши тему исследования.")

@bot.message_handler(func=lambda message: True)
def handle_task(message):
    task_description = message.text
    bot.send_message(message.chat.id, f"🚀 Принято! Запускаю Рой для задачи: '{task_description}'\n⏳ Это займет около минуты...")
    
    try:
        # Запускаем наш основной движок как отдельный процесс
        # Используем Python из venv!
        venv_python = os.path.join(script_dir, "venv", "Scripts", "python.exe")
        core_engine = os.path.join(script_dir, "core_engine.py")
        
        # Передаём все переменные окружения включая ключи из .env
        env = os.environ.copy()
        env.update(env_vars)  # Добавляем ключи из .env
        
        result = subprocess.run(
            [venv_python, core_engine], 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            env=env,
            cwd=script_dir
        )
        
        if result.returncode == 0:
            bot.send_message(message.chat.id, "✅ Задача выполнена! Файл с отчетом создан в безопасной зоне.")
            # Отправляем сам файл пользователю в Телеграм (из workspace)
            workspace_dir = os.path.join(script_dir, "workspace")
            output_file = os.path.join(workspace_dir, "trends_2026.md")
            if os.path.exists(output_file):
                with open(output_file, "rb") as file:
                    bot.send_document(message.chat.id, file)
            else:
                # Проверяем старое расположение для совместимости
                old_file = os.path.join(script_dir, "trends_2026.md")
                if os.path.exists(old_file):
                    with open(old_file, "rb") as file:
                        bot.send_document(message.chat.id, file)
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка в Рое: {result.stderr[:500]}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Критическая ошибка моста: {str(e)}")

if __name__ == "__main__":
    print("📲 Мост Telegram запущен. Напиши боту!")
    bot.polling()

