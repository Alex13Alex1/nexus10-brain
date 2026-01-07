# ═══════════════════════════════════════════════════════════════
#            👁️ OBSERVER.PY - AI Factory v0.7 Nexus
#              Фоновый SRE агент-наблюдатель (The Loop)
# ═══════════════════════════════════════════════════════════════

"""
Observer - фоновый процесс для мониторинга здоровья проектов.

Функции:
- Проверка Docker контейнеров
- Мониторинг HTTP endpoints
- Анализ логов на ошибки
- Автоматическое исцеление при сбоях
- Уведомления в Dashboard

Использование:
    python observer.py --project ./projects/MyApp --interval 300
    
Или как модуль:
    from observer import Observer
    obs = Observer("./projects/MyApp")
    obs.start()
"""

import os
import sys
import json
import time
import threading
import argparse
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any

# Исправление кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Импорт инструментов
from tools import (
    check_system_health,
    check_http_health,
    deploy_docker,
    stop_docker,
    get_docker_logs,
    read_file_safe,
    write_file_safe
)


# ═══════════════════════════════════════════════════════════════
#                    🏥 OBSERVER CLASS
# ═══════════════════════════════════════════════════════════════

class Observer:
    """
    SRE Observer - мониторит здоровье проекта и инициирует самоисцеление.
    
    Цикл: Check Health -> Analyze -> Fix -> Redeploy -> Verify
    """
    
    def __init__(
        self,
        project_path: str,
        check_interval: int = 300,  # 5 минут
        max_healing_attempts: int = 3,
        on_status_change: Optional[Callable] = None,
        on_healing_start: Optional[Callable] = None,
        on_healing_complete: Optional[Callable] = None
    ):
        """
        Args:
            project_path: Путь к проекту
            check_interval: Интервал проверки в секундах
            max_healing_attempts: Максимум попыток исцеления
            on_status_change: Callback при изменении статуса
            on_healing_start: Callback при начале исцеления
            on_healing_complete: Callback при завершении исцеления
        """
        self.project_path = os.path.abspath(project_path)
        self.check_interval = check_interval
        self.max_healing_attempts = max_healing_attempts
        
        # Callbacks
        self.on_status_change = on_status_change
        self.on_healing_start = on_healing_start
        self.on_healing_complete = on_healing_complete
        
        # State
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_status = "unknown"
        self._consecutive_failures = 0
        self._healing_in_progress = False
        
        # History
        self._history: List[Dict[str, Any]] = []
        self._healing_history: List[Dict[str, Any]] = []
        
        # Paths
        self._status_file = os.path.join(project_path, "monitoring", "live_status.json")
        self._history_file = os.path.join(project_path, "monitoring", "observer_history.json")
        self._healing_log_file = os.path.join(project_path, "monitoring", "healing_log.json")
        
        # Ensure directories exist
        os.makedirs(os.path.join(project_path, "monitoring"), exist_ok=True)
        os.makedirs(os.path.join(project_path, "logs"), exist_ok=True)
    
    # ═══════════════════════════════════════════════════════════
    #                    PUBLIC API
    # ═══════════════════════════════════════════════════════════
    
    def start(self):
        """Запускает Observer в фоновом потоке."""
        if self._running:
            print("⚠️ Observer already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._main_loop, daemon=True)
        self._thread.start()
        
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║              👁️ OBSERVER STARTED                                 ║
╠══════════════════════════════════════════════════════════════════╣
║  📁 Project: {self.project_path[:45]:<45} ║
║  ⏱️  Interval: {self.check_interval} seconds{' '*35}║
║  🔄 Max healing attempts: {self.max_healing_attempts}{' '*35}║
╚══════════════════════════════════════════════════════════════════╝
        """)
    
    def stop(self):
        """Останавливает Observer."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        
        # Save final status
        self._save_status({
            "status": "stopped",
            "timestamp": datetime.now().isoformat(),
            "stopped_by": "user"
        })
        
        print("⏹️ Observer stopped")
    
    def check_now(self) -> Dict[str, Any]:
        """Выполняет немедленную проверку."""
        return self._perform_health_check()
    
    def heal_now(self) -> Dict[str, Any]:
        """Принудительно запускает процесс исцеления."""
        return self._perform_healing("manual")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def current_status(self) -> str:
        return self._current_status
    
    @property
    def history(self) -> List[Dict[str, Any]]:
        return self._history[-100:]  # Последние 100 записей
    
    # ═══════════════════════════════════════════════════════════
    #                    MAIN LOOP
    # ═══════════════════════════════════════════════════════════
    
    def _main_loop(self):
        """Основной цикл мониторинга."""
        check_count = 0
        
        while self._running:
            check_count += 1
            
            print(f"\n{'═'*50}")
            print(f"👁️ OBSERVER CHECK #{check_count}")
            print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'═'*50}")
            
            # Perform health check
            health = self._perform_health_check()
            
            # Handle status change
            if health["overall"] != self._current_status:
                old_status = self._current_status
                self._current_status = health["overall"]
                self._on_status_changed(old_status, health["overall"])
            
            # Decide action based on status
            if health["overall"] == "healthy":
                self._consecutive_failures = 0
                print(f"✅ System healthy")
                
            elif health["overall"] in ["critical", "degraded"]:
                self._consecutive_failures += 1
                print(f"🚨 Issues detected! (Failures: {self._consecutive_failures})")
                
                # Trigger healing if not already in progress
                if not self._healing_in_progress:
                    if self._consecutive_failures >= 2:  # 2 consecutive failures
                        self._perform_healing("auto")
            
            else:
                print(f"⚪ Status: {health['overall']}")
            
            # Save current status
            self._save_status(health)
            
            # Wait for next check
            if self._running:
                time.sleep(self.check_interval)
    
    # ═══════════════════════════════════════════════════════════
    #                    HEALTH CHECKS
    # ═══════════════════════════════════════════════════════════
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Выполняет комплексную проверку здоровья."""
        health = check_system_health(self.project_path)
        
        # Add observer metadata
        health["observer"] = {
            "check_time": datetime.now().isoformat(),
            "consecutive_failures": self._consecutive_failures,
            "healing_in_progress": self._healing_in_progress
        }
        
        # Log to history
        self._history.append(health)
        if len(self._history) > 1000:
            self._history = self._history[-500:]  # Keep last 500
        
        # Print status
        print(f"   🐳 Docker: {health['docker']}")
        print(f"   🌐 HTTP: {health['http']}")
        print(f"   📜 Logs: {health['logs']}")
        print(f"   {'✅' if health['overall'] == 'healthy' else '⚠️'} Overall: {health['overall'].upper()}")
        
        if health["errors"]:
            print(f"   ❌ Errors: {', '.join(health['errors'][:3])}")
        
        return health
    
    # ═══════════════════════════════════════════════════════════
    #                    HEALING
    # ═══════════════════════════════════════════════════════════
    
    def _perform_healing(self, trigger: str) -> Dict[str, Any]:
        """
        Выполняет процесс самоисцеления.
        
        Args:
            trigger: Причина запуска ("auto" или "manual")
        """
        self._healing_in_progress = True
        
        healing_record = {
            "timestamp": datetime.now().isoformat(),
            "trigger": trigger,
            "attempts": [],
            "success": False,
            "final_status": "unknown"
        }
        
        print(f"\n{'🔄'*25}")
        print(f"🏥 HEALING PROCESS STARTED")
        print(f"   Trigger: {trigger}")
        print(f"{'🔄'*25}\n")
        
        if self.on_healing_start:
            self.on_healing_start(healing_record)
        
        # Try healing up to max_healing_attempts times
        for attempt in range(1, self.max_healing_attempts + 1):
            print(f"\n🔧 Healing attempt {attempt}/{self.max_healing_attempts}")
            
            attempt_record = {
                "attempt": attempt,
                "timestamp": datetime.now().isoformat(),
                "actions": [],
                "result": "pending"
            }
            
            # Get current health
            health = check_system_health(self.project_path)
            
            # Perform healing actions based on issues
            if health["docker"] in ["crashed", "not_found"]:
                print("   🐳 Restarting Docker...")
                success, msg = deploy_docker(self.project_path)
                attempt_record["actions"].append({
                    "action": "docker_restart",
                    "success": success,
                    "message": msg
                })
                print(f"   {'✅' if success else '❌'} {msg}")
                
                if success:
                    time.sleep(10)  # Wait for container to start
            
            elif health["http"] == "unreachable":
                print("   🌐 HTTP unreachable, checking container...")
                logs = get_docker_logs("app", 20)
                attempt_record["actions"].append({
                    "action": "check_logs",
                    "logs": logs[-500:]
                })
                
                # Try restart
                success, msg = deploy_docker(self.project_path)
                attempt_record["actions"].append({
                    "action": "container_rebuild",
                    "success": success,
                    "message": msg
                })
                
                if success:
                    time.sleep(15)  # Wait longer for rebuild
            
            elif health["logs"] == "errors_found":
                print("   📜 Errors in logs detected")
                attempt_record["actions"].append({
                    "action": "flagged_for_review",
                    "message": "Error logs detected, flagged for code review"
                })
            
            # Verify healing
            new_health = check_system_health(self.project_path)
            
            if new_health["overall"] == "healthy":
                attempt_record["result"] = "success"
                healing_record["success"] = True
                healing_record["final_status"] = "healthy"
                print(f"\n✅ HEALING SUCCESSFUL on attempt {attempt}!")
                break
            else:
                attempt_record["result"] = "failed"
                print(f"   ⚠️ Still unhealthy: {new_health['overall']}")
            
            healing_record["attempts"].append(attempt_record)
            
            if attempt < self.max_healing_attempts:
                print(f"   ⏳ Waiting before next attempt...")
                time.sleep(30)
        
        # Final status
        if not healing_record["success"]:
            final_health = check_system_health(self.project_path)
            healing_record["final_status"] = final_health["overall"]
            print(f"\n❌ HEALING FAILED after {self.max_healing_attempts} attempts")
            print(f"   Final status: {final_health['overall']}")
        
        # Save healing record
        self._healing_history.append(healing_record)
        self._save_healing_log()
        
        self._healing_in_progress = False
        self._consecutive_failures = 0
        
        if self.on_healing_complete:
            self.on_healing_complete(healing_record)
        
        return healing_record
    
    # ═══════════════════════════════════════════════════════════
    #                    CALLBACKS
    # ═══════════════════════════════════════════════════════════
    
    def _on_status_changed(self, old_status: str, new_status: str):
        """Вызывается при изменении статуса."""
        print(f"\n📢 STATUS CHANGED: {old_status} → {new_status}")
        
        if self.on_status_change:
            self.on_status_change(old_status, new_status)
    
    # ═══════════════════════════════════════════════════════════
    #                    PERSISTENCE
    # ═══════════════════════════════════════════════════════════
    
    def _save_status(self, health: Dict[str, Any]):
        """Сохраняет текущий статус в файл."""
        write_file_safe(self._status_file, json.dumps(health, indent=2, ensure_ascii=False))
    
    def _save_healing_log(self):
        """Сохраняет лог исцелений."""
        write_file_safe(
            self._healing_log_file,
            json.dumps(self._healing_history[-50:], indent=2, ensure_ascii=False)
        )


# ═══════════════════════════════════════════════════════════════
#                    STANDALONE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def quick_check(project_path: str) -> Dict[str, Any]:
    """Быстрая проверка здоровья без запуска Observer."""
    return check_system_health(project_path)


def run_observer_daemon(
    project_path: str,
    interval: int = 300,
    duration_hours: float = 24
):
    """
    Запускает Observer как демон на заданное время.
    
    Args:
        project_path: Путь к проекту
        interval: Интервал проверки в секундах
        duration_hours: Длительность работы в часах
    """
    obs = Observer(project_path, check_interval=interval)
    obs.start()
    
    try:
        # Run for specified duration
        end_time = time.time() + (duration_hours * 3600)
        while time.time() < end_time and obs.is_running:
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    finally:
        obs.stop()


# ═══════════════════════════════════════════════════════════════
#                    CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="👁️ AI Factory Observer - SRE Monitoring Agent"
    )
    
    parser.add_argument(
        "--project", "-p",
        type=str,
        required=True,
        help="Path to project directory"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)"
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=float,
        default=24,
        help="Run duration in hours (default: 24)"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Perform single health check and exit"
    )
    
    parser.add_argument(
        "--heal",
        action="store_true",
        help="Perform healing and exit"
    )
    
    args = parser.parse_args()
    
    # Validate project path
    if not os.path.exists(args.project):
        print(f"❌ Project not found: {args.project}")
        sys.exit(1)
    
    # Single check mode
    if args.check_only:
        health = quick_check(args.project)
        print(json.dumps(health, indent=2, ensure_ascii=False))
        sys.exit(0 if health["overall"] == "healthy" else 1)
    
    # Heal mode
    if args.heal:
        obs = Observer(args.project)
        result = obs.heal_now()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["success"] else 1)
    
    # Daemon mode
    run_observer_daemon(args.project, args.interval, args.duration)


if __name__ == "__main__":
    main()



















