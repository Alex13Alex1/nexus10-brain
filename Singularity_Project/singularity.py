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
from fpdf import FPDF

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

# 1. Загрузка окружения (override=True перезаписывает системные переменные!)
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, ".env")
load_dotenv(env_path, override=True)

# Проверка ключа перед стартом
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ ОШИБКА: Ключ OPENAI_API_KEY не найден в .env")
    exit()
print(f"✅ API Key loaded: {api_key[:20]}...")

# Песочница для безопасной записи файлов
WORKING_DIR = "workspace"
if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)
    print(f"📁 Создана безопасная зона: {WORKING_DIR}/")

# --- ФУНКЦИИ ЭКСПОРТА В РАЗНЫЕ ФОРМАТЫ ---

def save_as_txt(content, filename="result.txt"):
    """Сохраняет результат в TXT файл"""
    filepath = os.path.join(WORKING_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📄 TXT файл создан: {filepath}")
    return filepath

def save_as_md(content, filename="result.md"):
    """Сохраняет результат в Markdown файл"""
    filepath = os.path.join(WORKING_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📝 MD файл создан: {filepath}")
    return filepath

def save_as_pdf(content, filename="result.pdf"):
    """Сохраняет результат в PDF файл"""
    filepath = os.path.join(WORKING_DIR, filename)
    
    pdf = FPDF()
    pdf.add_page()
    
    # Добавляем шрифт с поддержкой Unicode (кириллица)
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=11)
    else:
        # Fallback на встроенный шрифт (без кириллицы)
        pdf.set_font("Helvetica", size=11)
    
    # Разбиваем текст на строки
    pdf.multi_cell(0, 10, content)
    pdf.output(filepath)
    
    print(f"📕 PDF файл создан: {filepath}")
    return filepath

def export_result(content, format="md"):
    """Экспортирует результат в указанном формате"""
    if format == "txt":
        return save_as_txt(content)
    elif format == "pdf":
        return save_as_pdf(content)
    else:  # default: md
        return save_as_md(content)

# 2. Инициализация инструментов
search_tool = SerperDevTool()
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))

# 3. База знаний (Память)
def save_to_memory(task, result):
    """Сохраняет результат в локальную базу данных"""
    conn = sqlite3.connect('singularity_memory.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS history (date TEXT, task TEXT, output TEXT)')
    cursor.execute("INSERT INTO history VALUES (?, ?, ?)", 
                   (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task, str(result)))
    conn.commit()
    conn.close()
    print("🧠 Память обновлена: опыт сохранен в базу данных.")

# 4. Создание Роя (динамически под задачу)
def create_crew(user_task):
    """Создаёт команду агентов для выполнения задачи"""
    
    # CEO - Оркестратор (использует настройки из .env автоматически)
    orchestrator = Agent(
        role='CEO Singularity (GPT-4o)',
        goal=f'Координировать выполнение задачи: {user_task}',
        backstory='Ты — высокоэффективный ИИ-директор. Твоя задача — идеальное исполнение воли Хозяина.',
        verbose=True,
        allow_delegation=True
    )

    # Офицер безопасности
    security_officer = Agent(
        role='Офицер Безопасности',
        goal='Проверять действия на наличие угроз и защищать систему',
        backstory='Ты гарантируешь, что код не выйдет за пределы папки workspace и не содержит уязвимостей.',
        verbose=True
    )

    # Техлид-Исследователь
    tech_lead = Agent(
        role='Техлид-Исследователь',
        goal='Собрать данные и подготовить финальный Markdown отчет',
        backstory='Ты лучший аналитик, использующий поиск для нахождения истины.',
        tools=[search_tool],
        verbose=True
    )

    # Описание задач
    research_task = Task(
        description=f"Проведи глубокое исследование по теме: {user_task}",
        expected_output="Детальный структурированный отчет на русском языке.",
        agent=tech_lead
    )

    security_task = Task(
        description="Проверь отчет на безопасность: нет ли API ключей, паролей, опасных команд.",
        expected_output="Подтверждение: БЕЗОПАСНО или список обнаруженных угроз.",
        agent=security_officer
    )

    save_task = Task(
        description="Запиши финальный результат в файл result.md в папке workspace",
        expected_output="Файл result.md создан в папке workspace.",
        agent=tech_lead,
        output_file=os.path.join(WORKING_DIR, "result.md")
    )

    return Crew(
        agents=[orchestrator, security_officer, tech_lead],
        tasks=[research_task, security_task, save_task],
        process=Process.sequential,
        verbose=True
    )

# 5. Telegram интерфейс
# Хранение настроек пользователя
user_settings = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = """🚀 *Singularity v1.0* [OpenAI Edition] готова к работе!

🤖 *Доступные агенты:*
• CEO Singularity — координация
• Офицер Безопасности — защита
• Техлид-Исследователь — поиск и анализ

📝 *Команды:*
/format\\_md — отчёт в Markdown (по умолчанию)
/format\\_txt — отчёт в TXT
/format\\_pdf — отчёт в PDF
/status — статус системы
/history — история задач

💡 Просто напиши задачу, например:
_"Найди топ-5 трендов в AI на 2026 год"_

🛡️ Все файлы создаются в безопасной зоне workspace/
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['format_md'])
def set_format_md(message):
    user_settings[message.chat.id] = {"format": "md"}
    bot.reply_to(message, "✅ Формат отчёта: *Markdown* (.md)", parse_mode='Markdown')

@bot.message_handler(commands=['format_txt'])
def set_format_txt(message):
    user_settings[message.chat.id] = {"format": "txt"}
    bot.reply_to(message, "✅ Формат отчёта: *Text* (.txt)", parse_mode='Markdown')

@bot.message_handler(commands=['format_pdf'])
def set_format_pdf(message):
    user_settings[message.chat.id] = {"format": "pdf"}
    bot.reply_to(message, "✅ Формат отчёта: *PDF* (.pdf)", parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def status(message):
    """Показывает статус системы"""
    status_text = f"""📊 *Статус Singularity v1.0*

✅ OpenAI API: {'Подключен' if os.getenv('OPENAI_API_KEY') else '❌ Не найден'}
✅ Serper API: {'Подключен' if os.getenv('SERPER_API_KEY') else '❌ Не найден'}
✅ Telegram: Активен
📁 Рабочая папка: {os.path.abspath(WORKING_DIR)}
"""
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['history'])
def show_history(message):
    """Показывает историю задач"""
    try:
        conn = sqlite3.connect('singularity_memory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT date, task FROM history ORDER BY date DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            history_text = "📜 *Последние 5 задач:*\n\n"
            for date, task in rows:
                history_text += f"• `{date}`: {task[:50]}...\n"
        else:
            history_text = "📜 История пуста. Отправь мне первую задачу!"
        
        bot.reply_to(message, history_text, parse_mode='Markdown')
    except:
        bot.reply_to(message, "📜 История пуста.")

@bot.message_handler(func=lambda message: True)
def handle_task(message):
    """Обрабатывает задачи от пользователя"""
    user_query = message.text
    
    # Получаем настройки формата пользователя
    settings = user_settings.get(message.chat.id, {"format": "md"})
    output_format = settings.get("format", "md")
    
    bot.send_message(message.chat.id, f"⚙️ Рой GPT-4o начал работу над задачей:\n_{user_query}_", parse_mode='Markdown')
    bot.send_message(message.chat.id, f"⏳ Это займёт 1-2 минуты... (формат: .{output_format})")
    
    try:
        # Создаём и запускаем Рой
        crew = create_crew(user_query)
        result = crew.kickoff()
        
        # Сохраняем в память
        save_to_memory(user_query, result)
        
        # Экспортируем в выбранном формате
        result_text = str(result)
        file_path = export_result(result_text, format=output_format)
        
        # Отправляем результат
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                bot.send_document(message.chat.id, file, caption=f"✅ Задача завершена! Формат: .{output_format}")
        else:
            bot.send_message(message.chat.id, f"✅ Готово!\n\n{result_text[:1000]}")
            
    except Exception as e:
        error_msg = str(e)[:500]
        bot.send_message(message.chat.id, f"❌ Ошибка: {error_msg}")
        print(f"ERROR: {e}")

# 6. Запуск
if __name__ == "__main__":
    print("=" * 50)
    print("💎 SINGULARITY v1.0 [OpenAI Edition]")
    print("=" * 50)
    print(f"✅ OpenAI API: {'OK' if os.getenv('OPENAI_API_KEY') else 'NOT FOUND'}")
    print(f"✅ Serper API: {'OK' if os.getenv('SERPER_API_KEY') else 'NOT FOUND'}")
    print(f"✅ Telegram: {'OK' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT FOUND'}")
    print(f"📁 Workspace: {os.path.abspath(WORKING_DIR)}")
    print("=" * 50)
    print("🚀 Ожидаю команды в Telegram...")
    print("=" * 50)
    
    bot.polling(none_stop=True)

