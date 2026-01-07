# ═══════════════════════════════════════════════════════════════
#            🧠 NEXUS v0.8 - AI Factory Ultra
#              Streamlined 6-Agent Architecture
# ═══════════════════════════════════════════════════════════════

import os
import sys
import time

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai_tools import FileReadTool
from dotenv import load_dotenv

load_dotenv(override=True)

# ═══════════════════════════════════════════════════════════════
#                    🤖 MODEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════

smart_llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)  # Maximum precision
fast_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)  # Maximum speed

# Tools
file_tool = FileReadTool()

# ═══════════════════════════════════════════════════════════════
#                    👥 AGENTS v0.8
# ═══════════════════════════════════════════════════════════════

researcher = Agent(
    role='Tech Researcher',
    goal='Найти современный стек и лучшие практики для {topic}',
    backstory='Ты анализируешь рынок ПО 2026 года и выбираешь самые стабильные и быстрые решения.',
    llm=fast_llm,
    verbose=True
)

architect = Agent(
    role='Solution Architect',
    goal='Спроектировать масштабируемую архитектуру и Mermaid-схему.',
    backstory='Ты проектируешь системы, которые не ломаются. Твой дизайн — фундамент успеха.',
    llm=smart_llm,
    verbose=True
)

coder = Agent(
    role='Senior Python Developer',
    goal='Написать эффективный код, Dockerfile и требования.',
    backstory='''Ты мастер Python. Ты пишешь код, который легко читать и быстро исполнять.
    
    КРИТИЧНО:
    - НИКОГДА не используй markdown (```) в выходных файлах
    - Пиши ТОЛЬКО чистый Python/YAML/Dockerfile
    - Начинай Python файлы с import или #
    ''',
    tools=[file_tool],
    llm=smart_llm,
    verbose=True
)

qa_engineer = Agent(
    role='QA Automation Engineer',
    goal='Проверить код на баги и запустить тесты.',
    backstory='Ты находишь ошибки раньше, чем они попадут в продакшн.',
    llm=smart_llm,
    verbose=True
)

evaluator = Agent(
    role='Performance Mentor',
    goal='Анализировать KPI кода (скорость/память) и проводить рефакторинг.',
    backstory='''Ты технический директор. Если код медленный — он не пройдет.
    
    Оценивай по критериям:
    - 🏎️ Производительность (Big O)
    - 🧹 Чистота (PEP8)
    - 🔒 Безопасность
    - 📦 Модульность
    
    Выставляй оценку 1-10.''',
    llm=smart_llm,
    verbose=True
)

sre_observer = Agent(
    role='SRE Observer',
    goal='Обеспечить 99.9% аптайма через самозаживление и мониторинг.',
    backstory='''Ты следишь за живой системой и лечишь её в реальном времени.
    
    ВАЖНО: Выводи ТОЛЬКО чистые конфиги (YAML, Dockerfile) БЕЗ markdown!''',
    llm=fast_llm,
    verbose=True
)

# ═══════════════════════════════════════════════════════════════
#                    🚀 NEXUS KICKOFF v0.8
# ═══════════════════════════════════════════════════════════════

def kickoff_nexus_v8(user_goal):
    """
    Запускает Nexus v0.8 с 6 агентами.
    
    Pipeline:
    Researcher → Architect → Coder → QA → Evaluator → SRE
    """
    
    # Create workspace
    clean_name = "".join(c for c in user_goal if c.isalnum() or c in (' ', '_')).strip()
    clean_name = clean_name.replace(' ', '_')[:25]
    workspace = f"./projects/{clean_name}"
    
    os.makedirs(f"{workspace}/source_code", exist_ok=True)
    os.makedirs(f"{workspace}/docs", exist_ok=True)
    os.makedirs(f"{workspace}/deployment", exist_ok=True)
    os.makedirs(f"{workspace}/tests", exist_ok=True)

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║              🧠 NEXUS v0.8 - AI Factory Ultra                    ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Workspace: {workspace:<48} ║
║  🎯 Goal: {user_goal[:50]:<53} ║
║                                                                  ║
║  👥 AGENTS (6):                                                  ║
║     🔍 Researcher    → Research best practices                   ║
║     🏗️  Architect     → Design architecture                      ║
║     👨‍💻 Coder         → Write code + Dockerfile                  ║
║     🧪 QA Engineer   → Test and validate                        ║
║     🎓 Evaluator     → Performance audit                        ║
║     🏥 SRE Observer  → Deploy config                            ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    # ═══════════════════════════════════════════════════════════
    #                    📋 TASKS
    # ═══════════════════════════════════════════════════════════

    task_research = Task(
        description=f'''Исследуй лучшие практики для: {user_goal}
        
        Найди:
        1. Актуальные библиотеки 2026 года
        2. Архитектурные паттерны
        3. Примеры реализации
        4. Потенциальные проблемы''',
        expected_output="Технический отчет с рекомендациями.",
        agent=researcher,
        output_file=f"{workspace}/docs/research.md"
    )

    task_arch = Task(
        description='''Создай архитектурную схему и ТЗ.
        
        Включи:
        1. Структуру модулей
        2. Потоки данных
        3. Mermaid диаграмму
        4. API контракты''',
        expected_output="Архитектурный документ с Mermaid схемой.",
        agent=architect,
        context=[task_research],
        output_file=f"{workspace}/docs/architecture.md"
    )

    task_coding = Task(
        description=f'''Реализуй проект: {user_goal}
        
        Создай:
        1. main.py — основной код (ЧИСТЫЙ Python, БЕЗ ```)
        2. requirements.txt — зависимости
        3. Dockerfile — контейнеризация
        
        КРИТИЧНО:
        - НЕ используй markdown в файлах!
        - Начинай main.py с import или #
        - Добавь if __name__ == "__main__" для демо''',
        expected_output="Готовый Python код.",
        agent=coder,
        context=[task_arch],
        output_file=f"{workspace}/source_code/main.py"
    )
    
    task_requirements = Task(
        description='''Создай requirements.txt
        
        - Только используемые библиотеки
        - Формат: library==version
        - БЕЗ markdown!''',
        expected_output="requirements.txt",
        agent=coder,
        context=[task_coding],
        output_file=f"{workspace}/source_code/requirements.txt"
    )

    task_qa = Task(
        description=f'''Проведи тесты кода: {workspace}/source_code/main.py
        
        1. Проверь синтаксис
        2. Проанализируй логику
        3. Найди edge cases
        
        Вердикт: PASSED ✅ или FAILED ❌''',
        expected_output="QA отчет с вердиктом.",
        agent=qa_engineer,
        context=[task_coding],
        output_file=f"{workspace}/tests/qa_report.md"
    )

    task_optimization = Task(
        description=f'''Проанализируй производительность кода.
        
        Оцени по шкале 1-10:
        - 🏎️ Производительность (Big O): __/10
        - 🧹 Чистота кода (PEP8): __/10
        - 🔒 Безопасность: __/10
        - 📦 Модульность: __/10
        - 📝 Документация: __/10
        
        ОБЩИЙ БАЛЛ: __/10
        
        Предложи ТОП-3 улучшения.''',
        expected_output="Performance audit с оценками и рекомендациями.",
        agent=evaluator,
        context=[task_coding, task_qa],
        output_file=f"{workspace}/docs/performance_audit.md"
    )

    task_deploy = Task(
        description='''Создай docker-compose.yml для деплоя.
        
        Включи:
        - version: '3.8'
        - services с app
        - volumes, networks
        - healthcheck
        - restart policy
        
        ВАЖНО: ТОЛЬКО чистый YAML, БЕЗ ```!''',
        expected_output="docker-compose.yml",
        agent=sre_observer,
        context=[task_optimization],
        output_file=f"{workspace}/deployment/docker-compose.yml"
    )
    
    task_dockerfile = Task(
        description='''Создай Dockerfile.
        
        - Multi-stage build
        - python:3.11-slim
        - Non-root user
        - Healthcheck
        
        ВАЖНО: ТОЛЬКО чистый Dockerfile, БЕЗ ```!''',
        expected_output="Dockerfile",
        agent=sre_observer,
        context=[task_coding, task_requirements],
        output_file=f"{workspace}/deployment/Dockerfile"
    )

    # ═══════════════════════════════════════════════════════════
    #                    🚀 CREW EXECUTION
    # ═══════════════════════════════════════════════════════════

    nexus_crew = Crew(
        agents=[researcher, architect, coder, qa_engineer, evaluator, sre_observer],
        tasks=[
            task_research,
            task_arch,
            task_coding,
            task_requirements,
            task_qa,
            task_optimization,
            task_deploy,
            task_dockerfile
        ],
        process=Process.sequential,
        memory=True,
        verbose=True
    )

    start_time = time.time()
    result = nexus_crew.kickoff(inputs={'topic': user_goal})
    elapsed = time.time() - start_time

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    ✅ NEXUS v0.8 COMPLETE!                       ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Output: {workspace:<51} ║
║  ⏱️  Time: {elapsed:.1f}s{' '*52}║
║                                                                  ║
║  📄 Files:                                                       ║
║     docs/research.md          — Tech research                    ║
║     docs/architecture.md      — Architecture + Mermaid           ║
║     docs/performance_audit.md — Quality score                    ║
║     source_code/main.py       — Application code                 ║
║     source_code/requirements.txt — Dependencies                  ║
║     tests/qa_report.md        — QA results                       ║
║     deployment/Dockerfile     — Docker image                     ║
║     deployment/docker-compose.yml — Deploy config                ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    return workspace, result


# ═══════════════════════════════════════════════════════════════
#                    🚀 MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              🧠 NEXUS v0.8 - AI Factory Ultra                    ║
║          6 Agents • Performance Audit • Auto-Deploy              ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    user_goal = input("🎯 Что создаём? ").strip()
    
    if user_goal:
        workspace, result = kickoff_nexus_v8(user_goal)
        print(f"\n📁 Проект готов: {workspace}")
    else:
        print("❌ Цель не указана")



















