import os
import sys
import subprocess
import base64

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from crewai_tools import FileReadTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

# Инициализация инструментов
file_tool = FileReadTool()

# ═══════════════════════════════════════════════════════════════
#               🔄 SELF-HEALING LOOP (The Loop)
# ═══════════════════════════════════════════════════════════════

import json
import time
from datetime import datetime

def check_system_health(project_path):
    """Проверяет здоровье системы и возвращает статус"""
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "docker": "unknown",
        "http": "unknown",
        "logs": "unknown",
        "overall": "unknown",
        "errors": [],
        "actions_taken": []
    }
    
    # 1. Проверка Docker
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=app", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        if "Up" in result.stdout:
            health_status["docker"] = "healthy"
        elif "Exited" in result.stdout:
            health_status["docker"] = "crashed"
            health_status["errors"].append("Docker container crashed")
        else:
            health_status["docker"] = "not_found"
    except:
        health_status["docker"] = "unavailable"
    
    # 2. Проверка HTTP
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:8080/health", timeout=5) as response:
            if response.getcode() == 200:
                health_status["http"] = "healthy"
            else:
                health_status["http"] = "degraded"
    except:
        health_status["http"] = "unreachable"
    
    # 3. Проверка логов
    log_file = os.path.join(project_path, "logs", "app.log")
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.read()
            if "ERROR" in logs or "Exception" in logs:
                health_status["logs"] = "errors_found"
                health_status["errors"].append("Errors in application logs")
            else:
                health_status["logs"] = "clean"
    else:
        health_status["logs"] = "no_logs"
    
    # 4. Определение общего статуса
    if health_status["docker"] == "crashed" or health_status["http"] == "unreachable":
        health_status["overall"] = "critical"
    elif health_status["logs"] == "errors_found" or health_status["http"] == "degraded":
        health_status["overall"] = "degraded"
    elif health_status["docker"] == "healthy" and health_status["http"] == "healthy":
        health_status["overall"] = "healthy"
    else:
        health_status["overall"] = "unknown"
    
    return health_status


def self_healing_cycle(project_path, max_attempts=3):
    """
    Цикл самоисцеления: Observer -> Analyze -> Fix -> Redeploy
    Continuous Improvement Loop
    """
    print(f"\n{'='*60}")
    print(f"🔄 SELF-HEALING CYCLE STARTED")
    print(f"📁 Project: {project_path}")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    healing_log = []
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔍 Attempt {attempt}/{max_attempts}")
        
        # Step 1: Check Health
        health = check_system_health(project_path)
        healing_log.append({
            "attempt": attempt,
            "health": health,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"   Docker: {health['docker']}")
        print(f"   HTTP: {health['http']}")
        print(f"   Logs: {health['logs']}")
        print(f"   Overall: {health['overall']}")
        
        # Step 2: If healthy, exit
        if health["overall"] == "healthy":
            print(f"\n✅ System is HEALTHY! No action needed.")
            break
        
        # Step 3: If critical, attempt fix
        if health["overall"] in ["critical", "degraded"]:
            print(f"\n🚨 Issues detected! Initiating self-healing...")
            
            # Action based on issue
            if health["docker"] == "crashed":
                print("   🐳 Restarting Docker container...")
                try:
                    subprocess.run(
                        ["docker-compose", "restart"],
                        cwd=os.path.join(project_path, "deploy"),
                        capture_output=True, timeout=60
                    )
                    health["actions_taken"].append("Restarted Docker container")
                except Exception as e:
                    print(f"   ❌ Restart failed: {e}")
            
            if health["http"] == "unreachable":
                print("   🌐 Application unreachable, checking container...")
                try:
                    # Try to rebuild
                    subprocess.run(
                        ["docker-compose", "up", "--build", "-d"],
                        cwd=os.path.join(project_path, "deploy"),
                        capture_output=True, timeout=300
                    )
                    health["actions_taken"].append("Rebuilt and restarted container")
                except Exception as e:
                    print(f"   ❌ Rebuild failed: {e}")
            
            if health["logs"] == "errors_found":
                print("   📜 Analyzing error logs...")
                health["actions_taken"].append("Flagged for code review")
            
            # Wait before next check
            if attempt < max_attempts:
                print(f"\n   ⏳ Waiting 10 seconds before next check...")
                time.sleep(10)
    
    # Save healing log
    log_path = os.path.join(project_path, "monitoring", "healing_log.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(healing_log, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Healing log saved to: {log_path}")
    
    return healing_log


def continuous_monitoring(project_path, interval_minutes=5, duration_hours=1):
    """
    Непрерывный мониторинг с автоматическим исцелением
    Запускается в отдельном потоке
    """
    import threading
    
    def monitor_loop():
        end_time = time.time() + (duration_hours * 3600)
        check_count = 0
        
        while time.time() < end_time:
            check_count += 1
            print(f"\n{'='*60}")
            print(f"🔄 MONITORING CHECK #{check_count}")
            print(f"{'='*60}")
            
            health = check_system_health(project_path)
            
            # Update status file for dashboard
            status_file = os.path.join(project_path, "monitoring", "live_status.json")
            os.makedirs(os.path.dirname(status_file), exist_ok=True)
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(health, f, indent=2, ensure_ascii=False)
            
            # If not healthy, trigger healing
            if health["overall"] not in ["healthy", "unknown"]:
                self_healing_cycle(project_path, max_attempts=2)
            
            # Wait for next check
            time.sleep(interval_minutes * 60)
    
    # Start in background thread
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    print(f"🔄 Continuous monitoring started (every {interval_minutes} min for {duration_hours} hour(s))")
    return thread


# ═══════════════════════════════════════════════════════════════
#      🔄 THE LOOP: Agent-Powered Continuous Improvement
# ═══════════════════════════════════════════════════════════════

def agent_powered_healing(project_path, error_context):
    """
    Полный цикл самоисцеления с использованием AI-агентов:
    Observer -> Analyzer -> Coder -> DevOps -> Deploy
    """
    from crewai import Agent, Task, Crew, Process
    
    print(f"\n{'🔄'*30}")
    print(f"🧠 AGENT-POWERED HEALING INITIATED")
    print(f"{'🔄'*30}\n")
    
    # Определяем LLM для агентов цикла
    healing_llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
    fast_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.1)
    
    # ═══════════════════════════════════════════════════════════
    # Агент 1: Error Analyzer (Анализатор ошибок)
    # ═══════════════════════════════════════════════════════════
    error_analyzer = Agent(
        role='Error Analyzer',
        goal='Проанализировать ошибку и определить корневую причину',
        backstory='''Ты эксперт по диагностике ошибок в Python приложениях.
        Ты читаешь логи, трейсбэки и определяешь точную причину сбоя.
        Ты даешь четкие инструкции по исправлению.''',
        llm=fast_llm,
        verbose=True
    )
    
    # ═══════════════════════════════════════════════════════════
    # Агент 2: Code Healer (Исцелитель кода)
    # ═══════════════════════════════════════════════════════════
    code_healer = Agent(
        role='Code Healer',
        goal='Исправить код на основе анализа ошибок',
        backstory='''Ты опытный Python разработчик, специализирующийся на исправлении багов.
        Ты пишешь ТОЛЬКО чистый Python код без markdown.
        НИКОГДА не используй ``` в своих файлах.
        Ты понимаешь паттерны ошибок и знаешь как их исправить.''',
        llm=healing_llm,
        verbose=True
    )
    
    # ═══════════════════════════════════════════════════════════
    # Агент 3: DevOps Healer (Исцелитель инфраструктуры)
    # ═══════════════════════════════════════════════════════════
    devops_healer = Agent(
        role='DevOps Healer',
        goal='Пересобрать и перезапустить приложение после исправлений',
        backstory='''Ты DevOps инженер. Ты управляешь Docker контейнерами.
        После исправления кода ты пересобираешь образ и запускаешь приложение.
        Ты проверяешь что всё работает корректно.''',
        llm=fast_llm,
        verbose=True
    )
    
    # ═══════════════════════════════════════════════════════════
    # Задачи для The Loop
    # ═══════════════════════════════════════════════════════════
    
    task_analyze = Task(
        description=f'''Проанализируй следующую ошибку и определи:
        1. Тип ошибки (SyntaxError, ImportError, RuntimeError и т.д.)
        2. Корневую причину
        3. Точные инструкции по исправлению
        4. Какие файлы нужно изменить
        
        Контекст ошибки:
        {error_context}
        
        Путь к проекту: {project_path}''',
        expected_output='Детальный анализ ошибки с инструкциями по исправлению',
        agent=error_analyzer,
        output_file=os.path.join(project_path, "monitoring", "error_analysis.md")
    )
    
    task_heal_code = Task(
        description=f'''На основе анализа ошибки исправь код.
        
        КРИТИЧЕСКИ ВАЖНО:
        - Прочитай файл {project_path}/source_code/main.py
        - Исправь найденные ошибки
        - Сохрани исправленную версию как main_healed.py
        - НИКОГДА не используй markdown (```) в коде
        - Пиши ТОЛЬКО чистый Python код
        
        Если ошибка связана с импортами:
        - Обнови requirements.txt
        - Используй только стандартные библиотеки где возможно''',
        expected_output='Исправленный Python код',
        agent=code_healer,
        context=[task_analyze],
        output_file=os.path.join(project_path, "source_code", "main_healed.py")
    )
    
    task_redeploy = Task(
        description=f'''После исправления кода:
        1. Проверь что main_healed.py существует и синтаксически корректен
        2. Скопируй main_healed.py в deploy/ папку
        3. Составь отчет о готовности к пересборке Docker
        
        Путь к проекту: {project_path}
        
        Выведи:
        - Статус исправления: READY / NOT_READY
        - Список изменённых файлов
        - Команды для пересборки''',
        expected_output='Отчет о готовности к деплою',
        agent=devops_healer,
        context=[task_heal_code],
        output_file=os.path.join(project_path, "monitoring", "redeploy_status.md")
    )
    
    # ═══════════════════════════════════════════════════════════
    # Запуск The Loop Crew
    # ═══════════════════════════════════════════════════════════
    
    healing_crew = Crew(
        agents=[error_analyzer, code_healer, devops_healer],
        tasks=[task_analyze, task_heal_code, task_redeploy],
        process=Process.sequential,
        verbose=True
    )
    
    try:
        result = healing_crew.kickoff()
        
        # Логируем результат
        healing_record = {
            "timestamp": datetime.now().isoformat(),
            "error_context": error_context[:500],  # Первые 500 символов
            "result": str(result)[:1000],
            "status": "completed"
        }
        
        # Сохраняем в историю исцелений
        history_file = os.path.join(project_path, "monitoring", "healing_history.json")
        history = []
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        history.append(healing_record)
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history[-10:], f, indent=2, ensure_ascii=False)  # Последние 10
        
        print(f"\n✅ AGENT-POWERED HEALING COMPLETED!")
        
        # Попытка пересборки Docker
        redeploy_status_file = os.path.join(project_path, "monitoring", "redeploy_status.md")
        if os.path.exists(redeploy_status_file):
            with open(redeploy_status_file, 'r', encoding='utf-8') as f:
                if "READY" in f.read():
                    print("🐳 Attempting Docker rebuild...")
                    try:
                        subprocess.run(
                            ["docker-compose", "up", "--build", "-d"],
                            cwd=os.path.join(project_path, "deploy"),
                            capture_output=True, timeout=300
                        )
                        print("✅ Docker rebuild successful!")
                    except Exception as e:
                        print(f"⚠️ Docker rebuild failed: {e}")
        
        return result
        
    except Exception as e:
        print(f"❌ HEALING FAILED: {e}")
        return None


def run_the_loop(project_path, check_interval_seconds=300, max_iterations=12):
    """
    THE LOOP: Непрерывный цикл улучшения
    Observer -> Coder -> DevOps -> Deploy -> Observer -> ...
    
    Args:
        project_path: Путь к проекту
        check_interval_seconds: Интервал проверки (по умолчанию 5 минут)
        max_iterations: Максимум итераций (по умолчанию 12 = 1 час)
    """
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        🔄 THE LOOP - Continuous Improvement Cycle            ║
║══════════════════════════════════════════════════════════════║
║  Observer → Analyzer → Coder → DevOps → Deploy → Observer    ║
╚══════════════════════════════════════════════════════════════╝
    
📁 Project: {project_path}
⏱️  Interval: {check_interval_seconds}s
🔄 Max iterations: {max_iterations}
    """)
    
    iteration = 0
    consecutive_healthy = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        print(f"\n{'═'*60}")
        print(f"🔄 THE LOOP - Iteration #{iteration}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'═'*60}")
        
        # Step 1: Observer checks health
        health = check_system_health(project_path)
        
        # Update live status for dashboard
        status_file = os.path.join(project_path, "monitoring", "live_status.json")
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(health, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Health Status:")
        print(f"   🐳 Docker: {health['docker']}")
        print(f"   🌐 HTTP: {health['http']}")
        print(f"   📜 Logs: {health['logs']}")
        print(f"   {'✅' if health['overall'] == 'healthy' else '⚠️'} Overall: {health['overall'].upper()}")
        
        # Step 2: Decide action
        if health["overall"] == "healthy":
            consecutive_healthy += 1
            print(f"\n✅ System healthy! (Streak: {consecutive_healthy})")
            
            # If healthy for 3 consecutive checks, reduce monitoring frequency
            if consecutive_healthy >= 3:
                print("💤 System stable. Extending check interval...")
                check_interval_seconds = min(check_interval_seconds * 1.5, 900)  # Max 15 min
                
        elif health["overall"] in ["critical", "degraded"]:
            consecutive_healthy = 0
            print(f"\n🚨 Issues detected! Starting healing process...")
            
            # Собираем контекст ошибки
            error_context = f"""
            Status: {health['overall']}
            Docker: {health['docker']}
            HTTP: {health['http']}
            Logs: {health['logs']}
            Errors: {', '.join(health['errors'])}
            """
            
            # Read actual logs if available
            log_file = os.path.join(project_path, "logs", "app.log")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    recent_logs = f.read()[-2000:]  # Last 2000 chars
                    error_context += f"\n\nRecent logs:\n{recent_logs}"
            
            # Step 3: Agent-powered healing
            agent_powered_healing(project_path, error_context)
            
            # Reset interval after healing
            check_interval_seconds = 60  # Check more frequently after healing
        
        else:
            print(f"\n⚪ Status unknown, continuing monitoring...")
        
        # Wait before next check
        if iteration < max_iterations:
            print(f"\n⏳ Next check in {check_interval_seconds:.0f} seconds...")
            time.sleep(check_interval_seconds)
    
    print(f"\n{'═'*60}")
    print(f"🏁 THE LOOP completed after {iteration} iterations")
    print(f"{'═'*60}")

# ═══════════════════════════════════════════════════════════════
#                    🔧 КАСТОМНЫЕ ИНСТРУМЕНТЫ
# ═══════════════════════════════════════════════════════════════

@tool
def execute_python_code(file_path: str) -> str:
    """Запускает Python файл и возвращает результат."""
    try:
        file_path = file_path.strip().strip('"').strip("'")
        if not os.path.exists(file_path):
            return f"❌ Файл не найден: {file_path}"
        
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(file_path) or '.'
        )
        
        output = ""
        if result.stdout: output += f"📤 STDOUT:\n{result.stdout}\n"
        if result.stderr: output += f"⚠️ STDERR:\n{result.stderr}\n"
        
        if result.returncode == 0:
            return f"✅ Успех (exit code: 0)\n{output}"
        return f"❌ Ошибка (exit code: {result.returncode})\n{output}"
    except subprocess.TimeoutExpired:
        return "⏰ Таймаут: > 30 секунд"
    except Exception as e:
        return f"💥 Сбой: {str(e)}"


@tool
def run_syntax_check(file_path: str) -> str:
    """Проверяет синтаксис Python файла."""
    try:
        file_path = file_path.strip().strip('"').strip("'")
        if not os.path.exists(file_path):
            return f"❌ Файл не найден: {file_path}"
        
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', file_path],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            return f"✅ Синтаксис OK: {file_path}"
        return f"❌ Ошибки:\n{result.stderr}"
    except Exception as e:
        return f"💥 Ошибка: {str(e)}"


# ═══════════════════════════════════════════════════════════════
#                    🏥 SRE HEALTH CHECK TOOLS
# ═══════════════════════════════════════════════════════════════

@tool
def check_docker_container_status(container_name: str = "app") -> str:
    """Проверяет статус Docker контейнера."""
    try:
        # Проверяем запущен ли Docker
        docker_check = subprocess.run(
            ["docker", "info"],
            capture_output=True, text=True, timeout=10
        )
        if docker_check.returncode != 0:
            return "❌ Docker не запущен или не установлен"
        
        # Получаем статус контейнера
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        
        if not result.stdout.strip():
            return f"⚠️ Контейнер '{container_name}' не найден"
        
        status = result.stdout.strip()
        
        if "Up" in status:
            # Проверяем health status
            health_result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name],
                capture_output=True, text=True, timeout=10
            )
            health = health_result.stdout.strip()
            
            if health == "healthy":
                return f"✅ HEALTHY: Контейнер '{container_name}' работает. Статус: {status}"
            elif health == "unhealthy":
                return f"🔴 UNHEALTHY: Контейнер работает, но проверка здоровья провалена!"
            else:
                return f"🟡 RUNNING: Контейнер '{container_name}' запущен. Статус: {status}"
        elif "Exited" in status:
            return f"🔴 CRASHED: Контейнер '{container_name}' остановлен. Статус: {status}"
        else:
            return f"⚠️ UNKNOWN: Статус контейнера: {status}"
            
    except Exception as e:
        return f"💥 Ошибка проверки Docker: {str(e)}"


@tool
def get_docker_logs(container_name: str = "app", lines: int = 50) -> str:
    """Получает последние логи Docker контейнера."""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(lines), container_name],
            capture_output=True, text=True, timeout=30
        )
        
        output = ""
        if result.stdout:
            output += f"📜 STDOUT (последние {lines} строк):\n{result.stdout}\n"
        if result.stderr:
            output += f"⚠️ STDERR:\n{result.stderr}\n"
        
        if not output:
            return f"📭 Логи пусты или контейнер '{container_name}' не найден"
        
        # Анализируем на критические ошибки
        errors_found = []
        critical_patterns = [
            "Error", "Exception", "Traceback", "CRITICAL", "FATAL",
            "500", "502", "503", "504", "ConnectionRefused", "ModuleNotFoundError"
        ]
        
        for line in output.split('\n'):
            for pattern in critical_patterns:
                if pattern in line:
                    errors_found.append(line.strip())
                    break
        
        if errors_found:
            output += f"\n🚨 КРИТИЧЕСКИЕ ОШИБКИ ({len(errors_found)}):\n"
            output += "\n".join(errors_found[:10])  # Первые 10
        
        return output
    except Exception as e:
        return f"💥 Ошибка получения логов: {str(e)}"


@tool
def health_check_http(url: str = "http://localhost:8080/health", timeout: int = 5) -> str:
    """Проверяет HTTP endpoint приложения."""
    try:
        import urllib.request
        import urllib.error
        
        req = urllib.request.Request(url, method='GET')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')[:500]
            
            if status_code == 200:
                return f"✅ HTTP 200 OK\nURL: {url}\nResponse: {body}"
            else:
                return f"⚠️ HTTP {status_code}\nURL: {url}\nResponse: {body}"
                
    except urllib.error.HTTPError as e:
        return f"🔴 HTTP ERROR {e.code}: {e.reason}\nURL: {url}"
    except urllib.error.URLError as e:
        return f"🔴 CONNECTION FAILED: {e.reason}\nURL: {url}\nПриложение недоступно!"
    except Exception as e:
        return f"💥 Health check failed: {str(e)}"


@tool
def analyze_app_logs(log_file_path: str) -> str:
    """Анализирует файл логов приложения на ошибки."""
    try:
        log_file_path = log_file_path.strip().strip('"').strip("'")
        
        if not os.path.exists(log_file_path):
            return f"📭 Файл логов не найден: {log_file_path}"
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            logs = f.read()
        
        # Ищем ошибки
        errors = []
        warnings = []
        
        for i, line in enumerate(logs.split('\n'), 1):
            line_lower = line.lower()
            if any(x in line_lower for x in ['error', 'exception', 'traceback', 'critical', 'fatal']):
                errors.append(f"L{i}: {line.strip()}")
            elif any(x in line_lower for x in ['warning', 'warn']):
                warnings.append(f"L{i}: {line.strip()}")
        
        report = f"📊 АНАЛИЗ ЛОГОВ: {log_file_path}\n"
        report += f"📝 Всего строк: {len(logs.split(chr(10)))}\n"
        report += f"🔴 Ошибок: {len(errors)}\n"
        report += f"🟡 Предупреждений: {len(warnings)}\n\n"
        
        if errors:
            report += "🚨 КРИТИЧЕСКИЕ ОШИБКИ:\n"
            report += "\n".join(errors[:15])  # Первые 15
            report += "\n\n"
        
        if warnings:
            report += "⚠️ ПРЕДУПРЕЖДЕНИЯ:\n"
            report += "\n".join(warnings[:10])  # Первые 10
        
        if not errors and not warnings:
            report += "✅ Критических проблем не обнаружено!"
        
        return report
        
    except Exception as e:
        return f"💥 Ошибка анализа логов: {str(e)}"


@tool
def create_incident_ticket(error_description: str, traceback: str = "", severity: str = "HIGH") -> str:
    """Создает тикет инцидента для срочного исправления."""
    import datetime
    
    ticket_id = f"INC-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    ticket = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    🚨 INCIDENT TICKET                            ║
╠══════════════════════════════════════════════════════════════════╣
║  ID: {ticket_id:<55} ║
║  Severity: {severity:<51} ║
║  Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<53} ║
╠══════════════════════════════════════════════════════════════════╣
║  DESCRIPTION:                                                    ║
║  {error_description[:60]:<60} ║
╠══════════════════════════════════════════════════════════════════╣
║  ACTION REQUIRED: Fix and redeploy                               ║
╚══════════════════════════════════════════════════════════════════╝

TRACEBACK:
{traceback[:1000] if traceback else 'N/A'}
"""
    return ticket


@tool
def analyze_image(image_path: str) -> str:
    """Анализирует изображение и возвращает описание."""
    try:
        from openai import OpenAI
        
        image_path = image_path.strip().strip('"').strip("'")
        if not os.path.exists(image_path):
            return f"❌ Изображение не найдено: {image_path}"
        
        # Читаем и кодируем изображение
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Определяем тип изображения
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/png')
        
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Проанализируй это изображение как UI/UX дизайнер и системный аналитик.
                            
Опиши подробно:
1. ТИП ИЗОБРАЖЕНИЯ: Что это? (скриншот интерфейса, схема БД, wireframe, диаграмма, набросок)
2. СТРУКТУРА: Какие основные блоки/секции/компоненты видны
3. ЭЛЕМЕНТЫ UI: Кнопки, поля ввода, меню, таблицы, карточки и т.д.
4. ЦВЕТОВАЯ СХЕМА: Основные цвета, стиль (темный/светлый)
5. ЛОГИКА: Какова предполагаемая логика работы
6. РЕКОМЕНДАЦИИ: Как это лучше реализовать в коде

Твой ответ будет использован программистом для создания кода."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Ошибка анализа изображения: {str(e)}"


# ═══════════════════════════════════════════════════════════════
#         🚀 АВТО-УСТАНОВЩИК
# ═══════════════════════════════════════════════════════════════

def install_dependencies(requirements_path: str) -> str:
    """Автоматически устанавливает библиотеки"""
    if not os.path.exists(requirements_path):
        return "📦 Файл requirements.txt не найден."
    
    with open(requirements_path, 'r') as f:
        content = f.read().strip()
    
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
    if not lines:
        return "📦 Нет внешних зависимостей."
    
    print(f"\n[🔧 Auto-Installer] Установка: {', '.join(lines)}")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_path, '-q'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            return f"✅ Установлено: {', '.join(lines)}"
        return f"⚠️ Проблема: {result.stderr}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


# ═══════════════════════════════════════════════════════════════
#                      📁 НАСТРОЙКА ПРОЕКТА
# ═══════════════════════════════════════════════════════════════

def setup_workspace(project_name):
    """Создает структуру папок"""
    clean = "".join(c for c in project_name if c.isalnum() or c in (' ', '_')).strip()
    clean = clean.replace(' ', '_')[:30]
    path = f"./projects/{clean}"
    
    for folder in ['docs', 'tech_specs', 'source_code', 'tests', 'reports', 'diagrams', 'deploy', 'vision', 'logs', 'monitoring']:
        os.makedirs(f"{path}/{folder}", exist_ok=True)
    return path


# ═══════════════════════════════════════════════════════════════
#              💰 МОДЕЛИ
# ═══════════════════════════════════════════════════════════════

smart_llm = ChatOpenAI(model_name="gpt-4o", temperature=0.2)
fast_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.1)
vision_llm = ChatOpenAI(model_name="gpt-4o", temperature=0.3, max_tokens=2000)

file_reader = FileReadTool()

# ═══════════════════════════════════════════════════════════════
#                      📸 РЕЖИМ РАБОТЫ
# ═══════════════════════════════════════════════════════════════

print("""
╔══════════════════════════════════════════════════════════════════╗
║          🏭 AI SOFTWARE FACTORY v8.0 (VISION)                    ║
║       👁️ Vision + 🧠 Memory + 🔄 Self-Heal + 🐳 Docker            ║
╚══════════════════════════════════════════════════════════════════╝
""")

# Проверяем наличие изображения для анализа
image_path = None
if os.path.exists("temp_vision.png"):
    image_path = os.path.abspath("temp_vision.png")
    print(f"👁️ Найдено изображение для анализа: {image_path}")
elif os.path.exists("vision_input.png"):
    image_path = os.path.abspath("vision_input.png")
    print(f"👁️ Найдено изображение для анализа: {image_path}")

user_goal = input("🎯 Какую задачу/программу реализуем сегодня? ")
workspace = setup_workspace(user_goal)

# ═══════════════════════════════════════════════════════════════
#                      👥 АГЕНТЫ (9 агентов)
# ═══════════════════════════════════════════════════════════════

# 👁️ Vision Analyst (НОВЫЙ!)
vision_analyst = Agent(
    role='Visual System Analyst',
    goal='Проанализировать изображение и составить детальное ТЗ.',
    backstory='''Ты — глаза системы. Ты видишь скриншоты, схемы, wireframes.
    Ты понимаешь:
    - Где кнопки и как они выглядят
    - Какие цвета используются
    - Какова логика интерфейса
    - Как связаны элементы
    
    Твой анализ помогает программисту воссоздать увиденное в коде.''',
    tools=[analyze_image],
    llm=vision_llm,
    verbose=True
)

# 💰 Оптимизатор ресурсов
cost_optimizer = Agent(
    role='Resource Optimizer',
    goal='Оценить сложность и оптимизировать ресурсы.',
    backstory='Эксперт по оптимизации API-затрат.',
    llm=fast_llm,
    verbose=True
)

# 🔍 Исследователь
researcher = Agent(
    role='Tech Researcher',
    goal='Найти лучшие практики и библиотеки для: {topic}',
    backstory='Следишь за трендами IT.',
    llm=fast_llm,
    verbose=True
)

# 🏗️ Архитектор
architect = Agent(
    role='Solution Architect',
    goal='Спроектировать архитектуру для: {topic}',
    backstory='Эксперт системного проектирования. Использует визуальный анализ если он есть.',
    llm=smart_llm,
    verbose=True
)

# 🎨 Визуализатор
visualizer = Agent(
    role='System Designer',
    goal='Создать Mermaid диаграмму архитектуры.',
    backstory='Мастер Mermaid.js синтаксиса.',
    llm=smart_llm,
    verbose=True
)

# 🔧 Инженер
engineer = Agent(
    role='System Engineer',
    goal='Подобрать технологии для: {topic}',
    backstory='Знает все библиотеки и фреймворки.',
    llm=smart_llm,
    verbose=True
)

# 👨‍💻 Разработчик
coder = Agent(
    role='Senior Python Developer',
    goal='Написать чистый Python код на основе архитектуры и визуального анализа.',
    backstory='''Мастер Python. PEP8, Clean Code.
    ⚠️ ЗАПРЕЩЕНО: ```python, markdown
    ✅ ТОЛЬКО чистый Python!
    Используешь визуальный анализ для точного воссоздания UI.''',
    llm=smart_llm,
    verbose=True
)

# 🔍 QA Инженер
qa_engineer = Agent(
    role='QA Automation Engineer',
    goal='Запустить код и найти ошибки.',
    backstory='Технический контролер. ЗАПУСКАЕТ код.',
    tools=[file_reader, run_syntax_check, execute_python_code],
    llm=fast_llm,
    verbose=True
)

# 📝 Technical Writer
tech_writer = Agent(
    role='Technical Writer',
    goal='Создать профессиональную документацию README.md.',
    backstory='Мастер документации. Твои README идеальны для GitHub.',
    llm=fast_llm,
    verbose=True
)

# 🐳 DevOps Engineer
devops_engineer = Agent(
    role='DevOps & Cloud Engineer',
    goal='Подготовить проект к запуску в любой среде через Docker и CI/CD.',
    backstory='''Ты мастер контейнеризации и автоматизации.
    
    КРИТИЧЕСКИ ВАЖНО:
    - НИКОГДА не используй markdown разметку (```)
    - Выводи ТОЛЬКО чистый текст файла
    - Без заголовков, без пояснений, только контент
    
    Ты создаешь:
    - Оптимизированные Dockerfile (multi-stage builds)
    - docker-compose.yml с правильными volumes и networks
    - .env.example с описанием переменных
    - GitHub Actions для CI/CD
    - Makefile для удобных команд''',
    llm=smart_llm,
    verbose=True
)

# 🏥 SRE Observer (Site Reliability Engineer) - НОВЫЙ!
sre_observer = Agent(
    role='SRE Observer (Site Reliability Engineer)',
    goal='Мониторить работу запущенного приложения и инициировать исправление при сбоях.',
    backstory='''Ты — страж стабильности и надежности системы.
    
    Твой девиз: "Zero Downtime"
    
    Твои обязанности:
    1. Проверять статус Docker контейнеров
    2. Анализировать логи на наличие ошибок (500, Exception, Traceback)
    3. Выполнять HTTP health checks
    4. Создавать incident tickets при обнаружении проблем
    5. Формировать отчеты для Кодера с полным трейсбэком
    
    Уровни severity:
    - CRITICAL: Приложение не отвечает / crash
    - HIGH: Ошибки 5xx, exceptions
    - MEDIUM: Warnings, медленные ответы
    - LOW: Информационные сообщения
    
    При обнаружении CRITICAL или HIGH — немедленно создай тикет!''',
    tools=[
        check_docker_container_status,
        get_docker_logs,
        health_check_http,
        analyze_app_logs,
        create_incident_ticket,
        file_tool
    ],
    llm=smart_llm,
    verbose=True
)

# ═══════════════════════════════════════════════════════════════
#                      📋 ЗАДАЧИ
# ═══════════════════════════════════════════════════════════════

tasks = []

# 👁️ Vision Task (если есть изображение)
if image_path:
    task_vision = Task(
        description=f'''👁️ ВИЗУАЛЬНЫЙ АНАЛИЗ:
        
        Изображение: {image_path}
        
        Используй инструмент analyze_image("{image_path}") для анализа.
        
        Создай детальное ТЗ:
        1. Тип изображения (UI, схема, wireframe)
        2. Структура и компоненты
        3. Элементы интерфейса
        4. Цветовая схема
        5. Логика работы
        6. Рекомендации по реализации''',
        expected_output="Детальное ТЗ на основе визуального анализа.",
        output_file=f"{workspace}/vision/visual_analysis.md",
        agent=vision_analyst
    )
    tasks.append(task_vision)

# 0️⃣ Анализ затрат
task_budget = Task(
    description='''Оцени задачу: {topic}
    1. Сложность (1-10)
    2. Что требует GPT-4o
    3. Что можно на Mini''',
    expected_output="План оптимизации.",
    output_file=f"{workspace}/reports/cost_analysis.md",
    agent=cost_optimizer,
    context=tasks.copy() if tasks else None
)
tasks.append(task_budget)

# 1️⃣ Исследование
task_research = Task(
    description='''Исследуй: {topic}
    Если есть визуальный анализ — учти его.
    1. Лучшие практики
    2. Библиотеки
    3. Потенциальные проблемы''',
    expected_output="Технический отчет.",
    output_file=f"{workspace}/reports/tech_research.md",
    agent=researcher,
    context=[task_budget]
)
tasks.append(task_research)

# 2️⃣ Архитектура
task_architecture = Task(
    description='''Архитектура для: {topic}
    ОБЯЗАТЕЛЬНО учти визуальный анализ если он есть!
    1. Модули
    2. Потоки данных
    3. Интерфейсы''',
    expected_output="Архитектурный план.",
    output_file=f"{workspace}/docs/architecture.md",
    agent=architect,
    context=[task_research] + ([tasks[0]] if image_path else [])
)
tasks.append(task_architecture)

# 3️⃣ Визуализация
task_visualize = Task(
    description='''Mermaid диаграмма архитектуры.
    flowchart TD, classDiagram или sequenceDiagram.''',
    expected_output="Mermaid диаграмма.",
    output_file=f"{workspace}/diagrams/architecture.md",
    agent=visualizer,
    context=[task_architecture]
)
tasks.append(task_visualize)

# 4️⃣ Технологии
task_tech_stack = Task(
    description='''Подбери технологии:
    Учти визуальный анализ для UI библиотек!
    1. Библиотеки с версиями
    2. Обоснование''',
    expected_output="Техническая спецификация.",
    output_file=f"{workspace}/tech_specs/technology_stack.md",
    agent=engineer,
    context=[task_architecture, task_research]
)
tasks.append(task_tech_stack)

# 5️⃣ Код
task_coding = Task(
    description=f'''Напиши код:
    - ТОЛЬКО чистый Python (БЕЗ ```)
    - Type hints + docstrings
    - Демо в if __name__ == "__main__"
    
    {"ВАЖНО: Используй визуальный анализ из vision/visual_analysis.md для точного воссоздания UI!" if image_path else ""}
    Предпочитай стандартные библиотеки!''',
    expected_output="Готовый Python код.",
    output_file=f"{workspace}/source_code/main.py",
    agent=coder,
    context=[task_architecture, task_tech_stack] + ([tasks[0]] if image_path else [])
)
tasks.append(task_coding)

# 6️⃣ Requirements
task_requirements = Task(
    description='''Создай requirements.txt:
    - Только реально используемые
    - БЕЗ markdown!''',
    expected_output="requirements.txt",
    output_file=f"{workspace}/source_code/requirements.txt",
    agent=coder,
    context=[task_coding]
)
tasks.append(task_requirements)

# 7️⃣ QA v1
task_review = Task(
    description=f'''ТЕСТИРОВАНИЕ:
    ФАЙЛ: {workspace}/source_code/main.py
    1. run_syntax_check
    2. execute_python_code
    Вердикт: PASSED ✅ или FAILED ❌''',
    expected_output="QA отчет.",
    output_file=f"{workspace}/tests/review_report.md",
    agent=qa_engineer,
    context=[task_coding]
)
tasks.append(task_review)

# 8️⃣ Self-Healing
task_healing = Task(
    description=f'''🔄 САМОВОССТАНОВЛЕНИЕ:
    Прочитай: {workspace}/tests/review_report.md
    ЕСЛИ ошибки → исправь
    ЕСЛИ PASSED → # No fixes needed
    ⚠️ ЗАПРЕЩЕНО: ```python
    ✅ Начинай с: import''',
    expected_output="Исправленный код.",
    output_file=f"{workspace}/source_code/main_fixed.py",
    agent=coder,
    context=[task_review, task_coding]
)
tasks.append(task_healing)

# 9️⃣ QA Final
task_final_review = Task(
    description=f'''ФИНАЛЬНАЯ ПРОВЕРКА:
    ФАЙЛ: {workspace}/source_code/main_fixed.py
    ВЕРДИКТ: ✅ PRODUCTION READY / ⚠️ NEEDS ATTENTION / ❌ CRITICAL''',
    expected_output="Финальный QA.",
    output_file=f"{workspace}/tests/final_report.md",
    agent=qa_engineer,
    context=[task_healing]
)
tasks.append(task_final_review)

# 🔟 Dockerfile (DevOps)
task_dockerfile = Task(
    description=f'''Создай оптимизированный Dockerfile:
    
    Требования:
    1. Multi-stage build для уменьшения размера
    2. python:3.11-slim как базовый образ
    3. Непривилегированный пользователь для безопасности
    4. Правильный порядок COPY для кэширования слоев
    5. Health check
    6. Labels с метаданными
    
    Формат: чистый Dockerfile БЕЗ markdown!''',
    expected_output="Оптимизированный Dockerfile.",
    output_file=f"{workspace}/deploy/Dockerfile",
    agent=devops_engineer,
    context=[task_coding, task_requirements]
)
tasks.append(task_dockerfile)

# 1️⃣1️⃣ docker-compose (DevOps)
task_docker_compose = Task(
    description=f'''Создай docker-compose.yml:
    
    Включи:
    1. version: '3.8'
    2. services с app
    3. build context
    4. environment из .env
    5. volumes для persistence
    6. networks
    7. restart policy
    8. healthcheck
    
    Формат: чистый YAML БЕЗ markdown!''',
    expected_output="docker-compose.yml",
    output_file=f"{workspace}/deploy/docker-compose.yml",
    agent=devops_engineer,
    context=[task_dockerfile]
)
tasks.append(task_docker_compose)

# 1️⃣2️⃣ .env.example (DevOps)
task_env_example = Task(
    description=f'''Создай .env.example:
    
    Включи все переменные окружения с описаниями:
    # Database
    DATABASE_URL=postgresql://user:pass@localhost:5432/db
    
    # API Keys
    API_KEY=your-api-key-here
    
    # App Settings
    DEBUG=false
    PORT=8000
    
    Формат: чистый .env БЕЗ markdown!''',
    expected_output=".env.example с описаниями.",
    output_file=f"{workspace}/deploy/.env.example",
    agent=devops_engineer,
    context=[task_coding]
)
tasks.append(task_env_example)

# 1️⃣3️⃣ Makefile (DevOps)
task_makefile = Task(
    description=f'''Создай Makefile с командами:
    
    .PHONY: help install run test docker-build docker-run clean
    
    help:          ## Показать справку
    install:       ## Установить зависимости
    run:           ## Запустить приложение
    test:          ## Запустить тесты
    docker-build:  ## Собрать Docker образ
    docker-run:    ## Запустить в Docker
    docker-stop:   ## Остановить контейнеры
    clean:         ## Очистить кэш
    
    Формат: чистый Makefile БЕЗ markdown!''',
    expected_output="Makefile.",
    output_file=f"{workspace}/Makefile",
    agent=devops_engineer,
    context=[task_dockerfile, task_docker_compose]
)
tasks.append(task_makefile)

# 1️⃣4️⃣ GitHub Actions CI/CD (DevOps)
task_cicd = Task(
    description=f'''Создай .github/workflows/ci.yml:
    
    name: CI/CD Pipeline
    
    on:
      push:
        branches: [main]
      pull_request:
        branches: [main]
    
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
          - pip install + pytest
      
      build:
        needs: test
        steps:
          - docker build
          - docker push (если main)
    
    Формат: чистый YAML БЕЗ markdown!''',
    expected_output="GitHub Actions workflow.",
    output_file=f"{workspace}/deploy/ci.yml",
    agent=devops_engineer,
    context=[task_dockerfile, task_requirements]
)
tasks.append(task_cicd)

# 1️⃣2️⃣ README
task_readme = Task(
    description=f'''README.md с:
    - Название и описание
    - Быстрый старт
    - Docker инструкции
    - Структура проекта
    - {"Визуальный анализ (если есть)" if image_path else "Архитектура"}
    Используй эмодзи!''',
    expected_output="README.md",
    output_file=f"{workspace}/README.md",
    agent=tech_writer,
    context=[task_architecture, task_visualize, task_dockerfile]
)
tasks.append(task_readme)

# ═══════════════════════════════════════════════════════════════
#                   🏥 SRE МОНИТОРИНГ (POST-DEPLOY)
# ═══════════════════════════════════════════════════════════════

# 1️⃣5️⃣ Health Check & Monitoring
task_monitoring = Task(
    description=f'''ПОСЛЕ деплоя выполни полную проверку системы:

    1. DOCKER STATUS:
       - Проверь статус контейнера через check_docker_container_status
       - Контейнер должен быть "Up" или "healthy"
    
    2. LOGS ANALYSIS:
       - Получи последние 100 строк логов через get_docker_logs
       - Ищи: Error, Exception, Traceback, 500, CRITICAL, FATAL
    
    3. HTTP HEALTH CHECK:
       - Проверь endpoint через health_check_http
       - Ожидаемый ответ: HTTP 200
    
    4. APP LOGS (если есть):
       - Проверь файл {workspace}/logs/app.log через analyze_app_logs
    
    5. ВЕРДИКТ:
       - Если всё ОК: "🟢 SYSTEM HEALTHY"
       - Если есть WARNING: "🟡 SYSTEM DEGRADED"
       - Если есть ERROR: "🔴 SYSTEM CRITICAL"
    
    6. При CRITICAL/HIGH ошибках:
       - Создай incident ticket через create_incident_ticket
       - Включи полный traceback''',
    expected_output='''Полный отчет о состоянии системы:
    - Docker status
    - Logs analysis
    - HTTP health check
    - Overall verdict
    - Incident ticket (если нужен)''',
    output_file=f"{workspace}/monitoring/health_report.md",
    agent=sre_observer,
    context=[task_dockerfile, task_docker_compose]
)
tasks.append(task_monitoring)

# 1️⃣6️⃣ Self-Healing Task (если найдены ошибки)
task_self_healing = Task(
    description=f'''Если SRE Observer обнаружил критические ошибки:

    1. Прочитай health_report.md
    2. Если есть incident ticket или статус "CRITICAL":
       
       ИСПРАВЬ КОД:
       - Найди причину ошибки в traceback
       - ModuleNotFoundError → добавь в requirements.txt
       - SyntaxError → исправь синтаксис
       - ConnectionError → проверь конфигурацию
       - 500 Error → исправь логику
       
    3. Сохрани исправленный код в {workspace}/source_code/main_healed.py
    4. Обнови requirements.txt если нужно
    
    ВАЖНО:
    - НЕ используй markdown (```)
    - Выводи ТОЛЬКО чистый Python код
    - Добавь комментарий: # Self-healed by AI at [timestamp]
    
    Если ошибок нет — напиши "No healing required. System healthy."''',
    expected_output="Исправленный код или подтверждение что система здорова.",
    output_file=f"{workspace}/source_code/main_healed.py",
    agent=coder,
    context=[task_monitoring, task_coding]
)
tasks.append(task_self_healing)

# ═══════════════════════════════════════════════════════════════
#                      🚀 ЗАПУСК
# ═══════════════════════════════════════════════════════════════

agents = [cost_optimizer, researcher, architect, visualizer, engineer, coder, qa_engineer, tech_writer, devops_engineer, sre_observer]
if image_path:
    agents.insert(0, vision_analyst)

crew = Crew(
    agents=agents,
    tasks=tasks,
    process=Process.sequential,
    memory=True,
    verbose=True
)

print(f"""
╔══════════════════════════════════════════════════════════════════╗
║       🚀 AI SOFTWARE FACTORY v10.0 (SELF-HEALING)                ║
║  👁️ Vision + 🐳 DevOps + 🏥 SRE + 🔄 Self-Healing + 🧠 Memory     ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Проект: {workspace:<50} ║
║  👁️ Vision: {"✅ АКТИВЕН" if image_path else "❌ Нет изображения":<47} ║
║                                                                  ║
║  👥 АГЕНТЫ ({len(agents)}):                                               ║
{"║     👁️ Vision Analyst  (4o)   — анализ изображений              ║" if image_path else ""}
║     💰 Cost Optimizer   (mini) — бюджет                          ║
║     🔍 Tech Researcher  (mini) — исследование                    ║
║     🏗️  Architect        (4o)   — архитектура                     ║
║     🎨 Visualizer       (4o)   — Mermaid                         ║
║     🔧 Engineer         (4o)   — технологии                      ║
║     👨‍💻 Developer        (4o)   — код                             ║
║     🔍 QA Engineer      (mini) — тестирование                    ║
║     📝 Tech Writer      (mini) — документация                    ║
║     🐳 DevOps Engineer  (4o)   — Docker + CI/CD                  ║
║     🏥 SRE Observer     (4o)   — мониторинг + self-healing       ║
║                                                                  ║
║  📋 ЗАДАЧИ: {len(tasks):<52} ║
╚══════════════════════════════════════════════════════════════════╝
""")

crew.kickoff(inputs={'topic': user_goal})

# Авто-установка
print("\n" + "="*60)
print("📦 АВТО-УСТАНОВЩИК")
print("="*60)
print(install_dependencies(f"{workspace}/source_code/requirements.txt"))

# Очистка временного файла
if os.path.exists("temp_vision.png"):
    os.remove("temp_vision.png")

print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           ✅ ПРОЕКТ ГОТОВ К ПРОДАКШЕНУ + МОНИТОРИНГ!             ║
╠══════════════════════════════════════════════════════════════════╣
{"║  👁️ vision/visual_analysis.md    — Визуальный анализ            ║" if image_path else ""}
║  📊 reports/cost_analysis.md       — Бюджет                      ║
║  🔍 reports/tech_research.md       — Исследование                ║
║  📄 docs/architecture.md           — Архитектура                 ║
║  🎨 diagrams/architecture.md       — Mermaid                     ║
║  🔧 tech_specs/technology_stack.md — Технологии                  ║
║  💻 source_code/main.py            — Код v1                      ║
║  🔄 source_code/main_fixed.py      — Код v2 (после QA)           ║
║  💊 source_code/main_healed.py     — Код v3 (self-healed)        ║
║  📦 source_code/requirements.txt   — Зависимости                 ║
║  🧪 tests/                         — QA отчеты                   ║
║  📝 README.md                      — Документация                ║
╠══════════════════════════════════════════════════════════════════╣
║  🐳 DEVOPS:                                                      ║
║     deploy/Dockerfile              — Оптимизированный образ      ║
║     deploy/docker-compose.yml      — Compose конфигурация        ║
║     deploy/.env.example            — Переменные окружения        ║
║     deploy/ci.yml                  — GitHub Actions CI/CD        ║
║     Makefile                       — Команды автоматизации       ║
╠══════════════════════════════════════════════════════════════════╣
║  🏥 SRE MONITORING (NEW!):                                       ║
║     monitoring/health_report.md    — Health Check отчет          ║
║     logs/                          — Логи приложения             ║
║                                                                  ║
║  Статусы системы:                                                ║
║     🟢 HEALTHY   — Всё работает                                  ║
║     🟡 DEGRADED  — Есть warnings                                 ║
║     🔴 CRITICAL  — Требуется исправление                         ║
╚══════════════════════════════════════════════════════════════════╝

🐳 Docker команды:
   make docker-build    # Собрать образ
   make docker-run      # Запустить контейнер
   make docker-stop     # Остановить

🏥 Self-Healing:
   При обнаружении ошибок SRE создает incident ticket
   Coder автоматически исправляет код → main_healed.py
   
🚀 CI/CD: Скопируй deploy/ci.yml в .github/workflows/

📁 Проверь папку: {workspace}
""")

# ═══════════════════════════════════════════════════════════════
#                 🔄 THE LOOP - Prompt to Start
# ═══════════════════════════════════════════════════════════════

print(f"""
╔══════════════════════════════════════════════════════════════════╗
║        🔄 THE LOOP - Continuous Improvement Available!           ║
╠══════════════════════════════════════════════════════════════════╣
║  Хочешь запустить непрерывный мониторинг и самоисцеление?        ║
║                                                                  ║
║  Что это делает:                                                 ║
║  • 👁️ Observer проверяет здоровье каждые 5 минут                 ║
║  • 🔍 Analyzer анализирует ошибки                                ║
║  • 👨‍💻 Coder автоматически исправляет код                         ║
║  • 🐳 DevOps пересобирает Docker                                 ║
║  • 🔄 Цикл повторяется до стабильности                           ║
╚══════════════════════════════════════════════════════════════════╝
""")

try:
    start_loop = input("Запустить The Loop? (y/n): ").strip().lower()
except EOFError:
    start_loop = 'n'  # По умолчанию не запускаем при pipe input

if start_loop == 'y':
    print("\n🔄 Starting The Loop...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        # Запускаем The Loop на 1 час (12 итераций по 5 минут)
        run_the_loop(
            project_path=workspace,
            check_interval_seconds=300,  # 5 минут
            max_iterations=12  # 1 час
        )
    except KeyboardInterrupt:
        print("\n\n⏹️ The Loop stopped by user")
        
        # Сохраняем финальный статус
        final_health = check_system_health(workspace)
        status_file = os.path.join(workspace, "monitoring", "live_status.json")
        os.makedirs(os.path.dirname(status_file), exist_ok=True)
        final_health["stopped_by"] = "user"
        final_health["stopped_at"] = datetime.now().isoformat()
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(final_health, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Final status saved to: {status_file}")
else:
    print("\n💡 Ты можешь запустить The Loop позже:")
    print(f"   from main import run_the_loop")
    print(f"   run_the_loop('{workspace}')")
