"""
NEXUS-6: Центральный Контроллер Автономной Системы
=================================================
6 Агентов | Big Data | Финансы | Автономный Цикл
"""
import sys
import time
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Windows UTF-8 fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from crewai import Crew, Process
from agents import NexusAgents
from tasks import NexusTasks
from database import NexusDB

# Инициализация базы данных
db = NexusDB()

def print_progress(stage, percent):
    bar = '=' * (percent // 5)
    space = ' ' * (20 - percent // 5)
    print("[{}{}] {}% | {}".format(bar, space, percent, stage))

def finalize_deal(project_name, amount, currency):
    """Финализация сделки с записью в базу данных"""
    project_id = db.add_project(project_name, amount, currency)
    print("💰 Проект '{}' зарегистрирован. Ожидаемая сумма: {} {}".format(project_name, amount, currency))
    
    # Имитация проверки платежа агентом-коллектором
    print("⏳ Ожидание подтверждения транзакции в {}...".format(currency))
    time.sleep(2)  # Агент проверяет API банка/кошелька
    
    db.mark_as_paid(project_id)
    print("✅ Оплата получена! Проект #{} переведен в статус PAID.".format(project_id))
    return project_id

def show_earnings():
    """Показать текущую прибыль"""
    earnings = db.get_total_earnings()
    stats = db.get_stats()
    
    print("\n" + "=" * 40)
    print("   📊 ФИНАНСОВЫЙ ОТЧЕТ NEXUS-6")
    print("=" * 40)
    print("Всего проектов: {}".format(stats['total_projects']))
    print("Оплачено: {}".format(stats['paid']))
    print("Ожидает оплаты: {}".format(stats['pending']))
    print("-" * 40)
    print("💵 ДОХОД ПО ВАЛЮТАМ:")
    if earnings:
        for currency, total in earnings:
            print("   {} : {:.2f}".format(currency, total))
    else:
        print("   Пока нет оплаченных проектов")
    print("=" * 40 + "\n")

def run_nexus():
    print("\n" + "=" * 60)
    print("   NEXUS-6: АВТОНОМНАЯ СИСТЕМА ВЫПОЛНЕНИЯ ЗАКАЗОВ")
    print("=" * 60 + "\n")
    
    print_progress("Инициализация системы Nexus-6", 10)
    agents = NexusAgents()
    tasks = NexusTasks()
    
    # Сборка команды из 6 агентов
    print_progress("Восстановление мозга агентов (Big Data)", 30)
    
    hunter = agents.hunter()
    architect = agents.architect()
    doer = agents.doer()
    qa = agents.qa_critic()
    collector = agents.collector()
    strategist = agents.strategist()
    
    nexus_crew = Crew(
        agents=[hunter, architect, doer, qa, collector, strategist],
        tasks=[
            tasks.hunt_task(hunter),
            tasks.execution_task(doer),
            tasks.qa_task(qa),
            tasks.invoice_task(collector)
        ],
        process=Process.sequential,
        verbose=True
    )

    print_progress("Запуск автономного цикла", 50)
    print("\n[NEXUS] Агенты начинают работу...\n")
    
    try:
        result = nexus_crew.kickoff()
        
        print_progress("Финальная верификация и выставление счета", 90)
        
        # Регистрация сделки в базе данных
        finalize_deal("Автономный проект", 500, "USD")
        
        print("\n" + "-" * 60)
        print("   ФИНАЛЬНЫЙ РЕЗУЛЬТАТ АВТОНОМНОЙ РАБОТЫ")
        print("-" * 60)
        print(result)
        
        # Показать финансовый отчет
        show_earnings()
        
        print_progress("Задача выполнена на 100%", 100)
        
    except Exception as e:
        print("\n[ERROR] Ошибка выполнения: {}".format(str(e)))
        print("[INFO] Проверьте OPENAI_API_KEY в .env файле")

if __name__ == "__main__":
    # Проверка ключей
    if not os.getenv('OPENAI_API_KEY'):
        print("[ERROR] OPENAI_API_KEY не найден в .env!")
        print("[INFO] Создайте .env файл с вашим ключом")
        sys.exit(1)
    
    run_nexus()
