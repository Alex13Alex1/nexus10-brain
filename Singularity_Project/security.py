"""
🛡️ МОДУЛЬ БЕЗОПАСНОСТИ SINGULARITY v1.0
Human-in-the-loop + Sandboxing
"""

import os
import json
from datetime import datetime

# Файл для обмена данными между ботом и движком
APPROVAL_FILE = "pending_approval.json"

# --- ОПАСНЫЕ ДЕЙСТВИЯ (требуют подтверждения) ---
DANGEROUS_KEYWORDS = [
    "delete", "remove", "drop", "truncate",  # Удаление
    "payment", "pay", "transfer", "send_money",  # Финансы
    "execute", "eval", "exec", "system",  # Выполнение кода
    "password", "credential", "secret",  # Чувствительные данные
    "api_key", "token",  # Ключи доступа
]

# --- БЕЗОПАСНЫЕ ДИРЕКТОРИИ (Sandbox) ---
ALLOWED_DIRECTORIES = [
    "workspace",  # Главная песочница!
    "reports",
    "output", 
    "exports",
]

class SecurityGuard:
    """Страж безопасности Singularity"""
    
    def __init__(self, script_dir=None):
        self.script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
        self.approval_file = os.path.join(self.script_dir, APPROVAL_FILE)
        self.log_file = os.path.join(self.script_dir, "security_log.txt")
    
    def is_dangerous_action(self, action_description: str) -> bool:
        """Проверяет, является ли действие опасным"""
        action_lower = action_description.lower()
        for keyword in DANGEROUS_KEYWORDS:
            if keyword in action_lower:
                return True
        return False
    
    def is_path_allowed(self, file_path: str) -> bool:
        """Проверяет, разрешён ли путь для записи (Sandbox)"""
        # Разрешаем запись в текущую директорию проекта
        abs_path = os.path.abspath(file_path)
        project_dir = os.path.abspath(self.script_dir)
        
        # Файл должен быть внутри проекта
        if not abs_path.startswith(project_dir):
            return False
        
        # Запрещаем изменение системных файлов
        forbidden = [".env", "security.py", "telegram_bridge.py", "core_engine.py"]
        filename = os.path.basename(file_path)
        if filename in forbidden:
            return False
        
        return True
    
    def request_approval(self, action: str, details: str) -> None:
        """Создаёт запрос на подтверждение (для Telegram бота)"""
        request = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details,
            "status": "pending"
        }
        with open(self.approval_file, 'w', encoding='utf-8') as f:
            json.dump(request, f, ensure_ascii=False, indent=2)
        
        self.log(f"⚠️ ЗАПРОС НА ПОДТВЕРЖДЕНИЕ: {action}")
    
    def check_approval(self) -> bool:
        """Проверяет, было ли получено подтверждение"""
        if not os.path.exists(self.approval_file):
            return True  # Нет запроса = разрешено
        
        with open(self.approval_file, 'r', encoding='utf-8') as f:
            request = json.load(f)
        
        return request.get("status") == "approved"
    
    def log(self, message: str) -> None:
        """Записывает в лог безопасности"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"🛡️ {message}")


def ask_human_permission(action_details: str) -> bool:
    """
    Запрашивает разрешение у человека через Telegram.
    В текущей версии просто логирует и продолжает.
    """
    guard = SecurityGuard()
    
    if guard.is_dangerous_action(action_details):
        guard.log(f"⚠️ ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ: {action_details}")
        guard.request_approval("dangerous_action", action_details)
        # В будущем здесь будет ожидание ответа от Telegram
        print(f"⚠️ ВНИМАНИЕ: Обнаружено потенциально опасное действие!")
        print(f"   Действие: {action_details}")
        return True  # Пока разрешаем (для тестирования)
    
    return True


def validate_file_write(file_path: str) -> bool:
    """Проверяет, можно ли записать в указанный файл"""
    guard = SecurityGuard()
    
    if not guard.is_path_allowed(file_path):
        guard.log(f"🚫 ЗАБЛОКИРОВАНО: Попытка записи в {file_path}")
        return False
    
    guard.log(f"✅ Разрешена запись в: {file_path}")
    return True

