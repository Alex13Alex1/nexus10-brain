"""
💎 SINGULARITY v1.0 [OpenAI Edition]
Автономная система AI-агентов с Telegram интерфейсом
"""

import os
import sys
import telebot
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# Windows UTF-8 fix
if sys.stdout:
    sys.stdout.reconfigure(encoding='utf-8')

# 1. Загрузка окружения
load_dotenv(override=True)

# Проверка ключей
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not OPENAI_KEY:
    print("❌ ОШИБКА: OPENAI_API_KEY не найден в .env")
    sys.exit(1)

# Песочница
WORKING_DIR = "workspace"
os.makedirs(WORKING_DIR, exist_ok=True)

# 2. Инструменты
search_tool = SerperDevTool()
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 3. База знаний
def save_to_memory(task, result):
    conn = sqlite3.connect('singularity_memory.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS history (date TEXT, task TEXT, output TEXT)')
    cursor.execute("INSERT INTO history VALUES (?, ?, ?)", 
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task, str(result)))
    conn.commit()
    conn.close()
    print("🧠 Память обновлена")

# 4. Создание Роя (АВТО-ЗАВОД 🏭)
def create_crew(user_task):
    """Создаёт команду агентов для СОЗДАНИЯ приложений"""
    
    # CEO - Координатор
    ceo = Agent(
        role='CEO Singularity',
        goal=f'Координировать создание приложения: {user_task}',
        backstory='Ты высокоэффективный ИИ-директор. Контролируешь весь процесс разработки.',
        verbose=True,
        allow_delegation=True
    )

    # Техлид - Архитектор
    tech_lead = Agent(
        role='Техлид-Архитектор',
        goal='Проектировать архитектуру и план разработки',
        backstory='Ты опытный архитектор ПО. Создаёшь чёткие планы и ТЗ.',
        tools=[search_tool],
        verbose=True
    )

    # Разработчик - Пишет код
    code_architect = Agent(
        role='Ведущий Разработчик (Python)',
        goal='Писать чистый, рабочий код на Python',
        backstory='Ты гений программирования. Твои скрипты работают с первого раза. Пиши код в файл.',
        # allow_code_execution=True,  # Требует Docker - отключено
        verbose=True
    )

    # Безопасник - Проверяет код
    security = Agent(
        role='Офицер Безопасности',
        goal='Проверять код на уязвимости и опасные функции',
        backstory='Ты эксперт по безопасности. Ни один баг не пройдёт мимо.',
        verbose=True
    )

    # Задача 1: Проектирование
    task_design = Task(
        description=f"Спроектируй архитектуру для задачи: {user_task}. Напиши пошаговый план.",
        expected_output="Техническое задание и план кода.",
        agent=tech_lead
    )

    # Задача 2: Написание кода
    task_coding = Task(
        description="Напиши Python-код согласно плану. Код должен быть чистым, с комментариями.",
        expected_output="Рабочий Python код.",
        agent=code_architect,
        output_file=os.path.join(WORKING_DIR, "app.py")
    )

    # Задача 3: Проверка безопасности
    task_review = Task(
        description="Проверь код на: 1) опасные функции (eval, exec), 2) утечки данных, 3) ошибки.",
        expected_output="Вердикт: БЕЗОПАСНО или список проблем.",
        agent=security
    )

    # Задача 4: Финальный отчёт
    task_report = Task(
        description="Создай README: что создано и как использовать.",
        expected_output="README с инструкцией.",
        agent=tech_lead,
        output_file=os.path.join(WORKING_DIR, "README.md")
    )

    return Crew(
        agents=[ceo, tech_lead, code_architect, security],
        tasks=[task_design, task_coding, task_review, task_report],
        process=Process.sequential,
        verbose=True
    )

# 5. Telegram
@bot.message_handler(commands=['start'])
def welcome(message):
    text = """🏭 *Singularity v1.0 — АВТО-ЗАВОД*

🤖 *Рой агентов:*
• CEO — координация проекта
• Техлид — архитектура и план
• Разработчик — пишет код
• Безопасник — проверяет код

⚙️ *Конвейер:*
1️⃣ Проектирование → ТЗ
2️⃣ Написание кода → app.py
3️⃣ Проверка безопасности
4️⃣ Документация → README.md

📝 Опиши, что создать:
• _Напиши телеграм-бот для заметок_
• _Создай парсер цен с сайта_
• _Сделай калькулятор расходов_
"""
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status(message):
    text = f"""📊 *Статус*
✅ OpenAI: {'OK' if OPENAI_KEY else '❌'}
✅ Serper: {'OK' if SERPER_KEY else '❌'}
✅ Telegram: OK
"""
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_task(message):
    query = message.text
    bot.send_message(message.chat.id, f"🏭 *Авто-завод* запущен!\n\nЗадача: _{query}_", parse_mode='Markdown')
    bot.send_message(message.chat.id, "⏳ Проектирование → Код → Проверка → Документация...")
    
    try:
        crew = create_crew(query)
        result = crew.kickoff()
        save_to_memory(query, result)
        
        # Отправляем созданные файлы
        app_path = os.path.join(WORKING_DIR, "app.py")
        readme_path = os.path.join(WORKING_DIR, "README.md")
        
        files_sent = 0
        if os.path.exists(app_path):
            with open(app_path, "rb") as f:
                bot.send_document(message.chat.id, f, caption="📦 Код приложения")
            files_sent += 1
        
        if os.path.exists(readme_path):
            with open(readme_path, "rb") as f:
                bot.send_document(message.chat.id, f, caption="📖 Документация")
            files_sent += 1
        
        if files_sent > 0:
            bot.send_message(message.chat.id, f"✅ *Готово!* Создано файлов: {files_sent}", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, f"✅ Готово!\n\n{str(result)[:1000]}")
            
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)[:500]}")
        print(f"ERROR: {e}")

# 6. Запуск
if __name__ == "__main__":
    print("=" * 50)
    print("💎 SINGULARITY v1.0 [OpenAI Edition]")
    print("=" * 50)
    print(f"✅ OpenAI: {OPENAI_KEY[:25]}..." if OPENAI_KEY else "❌ OpenAI: NOT FOUND")
    print(f"✅ Serper: OK" if SERPER_KEY else "⚠️ Serper: NOT FOUND")
    print(f"✅ Telegram: OK" if TELEGRAM_TOKEN else "❌ Telegram: NOT FOUND")
    print(f"📁 Workspace: {os.path.abspath(WORKING_DIR)}")
    print("=" * 50)
    print("🚀 Запущена на модели gpt-4o-mini...")
    print("📲 Ожидаю команды в Telegram...")
    print("=" * 50)
    
    bot.polling(none_stop=True)


