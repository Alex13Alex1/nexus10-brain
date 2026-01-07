# ═══════════════════════════════════════════════════════════════
#              🔧 TOOLS.PY - AI Factory v0.7 Nexus
#                    Набор инструментов агентов
# ═══════════════════════════════════════════════════════════════

import os
import sys
import subprocess
import base64
from datetime import datetime
from typing import Optional

from crewai.tools import tool
from crewai_tools import FileReadTool

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Глобальный инструмент для чтения файлов
file_tool = FileReadTool()


# ═══════════════════════════════════════════════════════════════
#                    🐍 CODE EXECUTION TOOLS
# ═══════════════════════════════════════════════════════════════

@tool
def execute_python_code(file_path: str) -> str:
    """
    Запускает Python файл и возвращает результат выполнения.
    Используй для тестирования сгенерированного кода.
    
    Args:
        file_path: Путь к Python файлу для выполнения
    
    Returns:
        Результат выполнения (stdout/stderr) или сообщение об ошибке
    """
    try:
        file_path = file_path.strip().strip('"').strip("'")
        
        if not os.path.exists(file_path):
            return f"❌ Файл не найден: {file_path}"
        
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(file_path) or '.',
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        )
        
        output = ""
        if result.stdout:
            output += f"📤 STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"⚠️ STDERR:\n{result.stderr}\n"
        
        if result.returncode == 0:
            return f"✅ Успех (exit code: 0)\n{output}"
        return f"❌ Ошибка (exit code: {result.returncode})\n{output}"
        
    except subprocess.TimeoutExpired:
        return "⏰ Таймаут: выполнение превысило 30 секунд"
    except Exception as e:
        return f"💥 Критический сбой: {str(e)}"


@tool
def run_syntax_check(file_path: str) -> str:
    """
    Проверяет синтаксис Python файла без выполнения.
    
    Args:
        file_path: Путь к Python файлу
    
    Returns:
        Результат проверки синтаксиса
    """
    try:
        file_path = file_path.strip().strip('"').strip("'")
        
        if not os.path.exists(file_path):
            return f"❌ Файл не найден: {file_path}"
        
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return f"✅ Синтаксис корректен: {file_path}"
        return f"❌ Синтаксическая ошибка:\n{result.stderr}"
        
    except Exception as e:
        return f"💥 Ошибка проверки: {str(e)}"


# ═══════════════════════════════════════════════════════════════
#                    👁️ VISION TOOLS
# ═══════════════════════════════════════════════════════════════

@tool
def analyze_image(image_path: str) -> str:
    """
    Анализирует изображение с помощью GPT-4o Vision.
    Извлекает UI элементы, цвета, структуру для воссоздания.
    
    Args:
        image_path: Путь к изображению (PNG, JPG, WEBP)
    
    Returns:
        Детальное описание изображения для разработчиков
    """
    try:
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        if not os.path.exists(image_path):
            return f"❌ Изображение не найдено: {image_path}"
        
        # Читаем и кодируем изображение
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Определяем MIME тип
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/png')
        
        # Создаем Vision LLM
        vision_llm = ChatOpenAI(model_name="gpt-4o", max_tokens=2000)
        
        # Формируем запрос
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Проанализируй это изображение как UI/UX эксперт.
                        
Предоставь ДЕТАЛЬНЫЙ технический отчет:

1. ТИП ИНТЕРФЕЙСА:
   - Веб-приложение / Мобильное / Десктоп / Дашборд / Форма

2. СТРУКТУРА LAYOUT:
   - Header / Sidebar / Main / Footer
   - Grid система (колонки, отступы)
   - Responsive breakpoints

3. КОМПОНЕНТЫ UI:
   - Кнопки (стили, размеры, состояния)
   - Формы (inputs, selects, checkboxes)
   - Карточки, таблицы, списки
   - Навигация (меню, tabs, breadcrumbs)

4. ЦВЕТОВАЯ ПАЛИТРА:
   - Primary color (HEX)
   - Secondary color (HEX)
   - Background (HEX)
   - Text colors (HEX)
   - Accent/CTA colors (HEX)

5. ТИПОГРАФИКА:
   - Заголовки (размер, вес)
   - Основной текст
   - Рекомендуемые шрифты

6. ИКОНКИ И ГРАФИКА:
   - Стиль иконок (outline/filled/duotone)
   - Иллюстрации
   - Изображения

7. РЕКОМЕНДАЦИИ ДЛЯ РАЗРАБОТЧИКА:
   - HTML структура
   - CSS framework (Tailwind/Bootstrap/Custom)
   - Ключевые классы стилей"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        response = vision_llm.invoke(messages)
        return f"👁️ ВИЗУАЛЬНЫЙ АНАЛИЗ:\n\n{response.content}"
        
    except Exception as e:
        return f"❌ Ошибка анализа изображения: {str(e)}"


# ═══════════════════════════════════════════════════════════════
#                    🐳 DOCKER TOOLS
# ═══════════════════════════════════════════════════════════════

def check_docker_available() -> bool:
    """Проверяет доступность Docker."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def deploy_docker(project_path: str, project_name: str = "app") -> tuple[bool, str]:
    """
    Собирает и запускает Docker контейнер для проекта.
    
    Args:
        project_path: Путь к проекту
        project_name: Имя контейнера
    
    Returns:
        (success: bool, message: str)
    """
    import shutil
    
    deploy_path = os.path.join(project_path, "deploy")
    dockerfile = os.path.join(deploy_path, "Dockerfile")
    
    if not os.path.exists(dockerfile):
        return False, "❌ Dockerfile не найден"
    
    # Копируем исходники в deploy
    source_code = os.path.join(project_path, "source_code")
    if os.path.exists(source_code):
        for f in os.listdir(source_code):
            src = os.path.join(source_code, f)
            dst = os.path.join(deploy_path, f)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
    
    try:
        # Останавливаем старые контейнеры
        subprocess.run(
            ["docker-compose", "down"],
            cwd=deploy_path,
            capture_output=True,
            timeout=30
        )
        
        # Собираем и запускаем
        result = subprocess.run(
            ["docker-compose", "up", "--build", "-d"],
            cwd=deploy_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, "✅ Контейнер успешно запущен!"
        return False, f"❌ Ошибка сборки:\n{result.stderr}"
        
    except subprocess.TimeoutExpired:
        return False, "⏰ Превышен таймаут сборки (5 мин)"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"


def stop_docker(project_path: str) -> bool:
    """Останавливает Docker контейнер проекта."""
    deploy_path = os.path.join(project_path, "deploy")
    try:
        result = subprocess.run(
            ["docker-compose", "down"],
            cwd=deploy_path,
            capture_output=True,
            timeout=30
        )
        return result.returncode == 0
    except:
        return False


def get_docker_logs(container_name: str = "app", tail: int = 50) -> str:
    """Получает логи Docker контейнера."""
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout + result.stderr
    except:
        return "Логи недоступны"


# ═══════════════════════════════════════════════════════════════
#                    📦 DEPENDENCY TOOLS
# ═══════════════════════════════════════════════════════════════

def install_dependencies(requirements_path: str) -> str:
    """
    Автоматически устанавливает зависимости из requirements.txt.
    
    Args:
        requirements_path: Путь к файлу requirements.txt
    
    Returns:
        Результат установки
    """
    if not os.path.exists(requirements_path):
        return "⚠️ requirements.txt не найден"
    
    # Проверяем содержимое
    with open(requirements_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    if not content or content.startswith('#') or len(content) < 3:
        return "ℹ️ requirements.txt пуст или содержит только комментарии"
    
    # Проверяем на невалидные строки
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]
    invalid_lines = [l for l in lines if ' ' in l and '==' not in l]
    
    if invalid_lines:
        return f"⚠️ Некорректный формат requirements.txt: {invalid_lines[0][:50]}..."
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', requirements_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return "✅ Все зависимости установлены"
        return f"⚠️ Проблема: {result.stderr[:200]}"
        
    except subprocess.TimeoutExpired:
        return "⏰ Таймаут установки (2 мин)"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


# ═══════════════════════════════════════════════════════════════
#                    🔍 HEALTH CHECK TOOLS
# ═══════════════════════════════════════════════════════════════

def check_http_health(url: str = "http://localhost:8080", timeout: int = 5) -> dict:
    """
    Проверяет HTTP endpoint.
    
    Returns:
        {"status": "healthy|unreachable|error", "code": int|None, "message": str}
    """
    import urllib.request
    import urllib.error
    
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return {
                "status": "healthy",
                "code": response.getcode(),
                "message": f"HTTP {response.getcode()} OK"
            }
    except urllib.error.HTTPError as e:
        return {
            "status": "error",
            "code": e.code,
            "message": f"HTTP {e.code}: {e.reason}"
        }
    except urllib.error.URLError as e:
        return {
            "status": "unreachable",
            "code": None,
            "message": str(e.reason)
        }
    except Exception as e:
        return {
            "status": "unreachable",
            "code": None,
            "message": str(e)
        }


def check_system_health(project_path: str) -> dict:
    """
    Комплексная проверка здоровья системы.
    
    Returns:
        Словарь со статусами всех компонентов
    """
    health = {
        "timestamp": datetime.now().isoformat(),
        "docker": "unknown",
        "http": "unknown",
        "logs": "unknown",
        "overall": "unknown",
        "errors": [],
        "actions_taken": []
    }
    
    # 1. Docker
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=app", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        if "Up" in result.stdout:
            health["docker"] = "healthy"
        elif "Exited" in result.stdout:
            health["docker"] = "crashed"
            health["errors"].append("Docker container crashed")
        else:
            health["docker"] = "not_found"
    except:
        health["docker"] = "unavailable"
    
    # 2. HTTP
    http_check = check_http_health()
    health["http"] = http_check["status"]
    if http_check["status"] != "healthy":
        health["errors"].append(f"HTTP: {http_check['message']}")
    
    # 3. Logs
    log_file = os.path.join(project_path, "logs", "app.log")
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            logs = f.read()
            if "ERROR" in logs or "Exception" in logs or "Traceback" in logs:
                health["logs"] = "errors_found"
                health["errors"].append("Errors in application logs")
            else:
                health["logs"] = "clean"
    else:
        health["logs"] = "no_logs"
    
    # 4. Overall
    if health["docker"] == "crashed" or health["http"] == "unreachable":
        health["overall"] = "critical"
    elif health["logs"] == "errors_found" or health["http"] == "error":
        health["overall"] = "degraded"
    elif health["docker"] == "healthy" and health["http"] == "healthy":
        health["overall"] = "healthy"
    else:
        health["overall"] = "unknown"
    
    return health


# ═══════════════════════════════════════════════════════════════
#                    📝 FILE TOOLS
# ═══════════════════════════════════════════════════════════════

def read_file_safe(filepath: str) -> Optional[str]:
    """Безопасное чтение файла."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return None
    return None


def write_file_safe(filepath: str, content: str) -> bool:
    """Безопасная запись файла с созданием директорий."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except:
        return False


# ═══════════════════════════════════════════════════════════════
#                    🧹 CODE CLEANING TOOLS
# ═══════════════════════════════════════════════════════════════

def strip_markdown_from_code(code: str) -> str:
    """
    Удаляет markdown разметку из кода.
    Решает проблему когда LLM добавляет ```python в код.
    """
    lines = code.split('\n')
    clean_lines = []
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Пропускаем markdown маркеры
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        # Пропускаем строки типа "```python" или "```yaml"
        if stripped.startswith('```'):
            continue
        
        clean_lines.append(line)
    
    result = '\n'.join(clean_lines).strip()
    
    # Если код начинается с описания вместо import, ищем первый import
    if result and not result.startswith(('import ', 'from ', '#', '"""', "'''")):
        import_idx = result.find('\nimport ')
        if import_idx == -1:
            import_idx = result.find('\nfrom ')
        if import_idx > 0:
            result = result[import_idx + 1:]
    
    return result


# ═══════════════════════════════════════════════════════════════
#                    📊 EXPORTS
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # Файловый инструмент
    'file_tool',
    
    # Code execution
    'execute_python_code',
    'run_syntax_check',
    
    # Vision
    'analyze_image',
    
    # Docker
    'check_docker_available',
    'deploy_docker',
    'stop_docker',
    'get_docker_logs',
    
    # Dependencies
    'install_dependencies',
    
    # Health checks
    'check_http_health',
    'check_system_health',
    
    # File operations
    'read_file_safe',
    'write_file_safe',
    
    # Code cleaning
    'strip_markdown_from_code',
]



















