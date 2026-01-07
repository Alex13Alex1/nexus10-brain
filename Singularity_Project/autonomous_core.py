# -*- coding: utf-8 -*-
"""
AUTONOMOUS CORE v1.0 - Self-Monitoring & Self-Healing System
=============================================================
- System Health Monitoring
- Automatic Error Recovery
- Performance Optimization
- Resource Management
- Intelligent Task Scheduling

Author: NEXUS 10 AI Agency
"""

import os
import sys
import time
import json
import sqlite3
import logging
import threading
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('autonomous.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AutonomousCore')


class SystemStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"


class TaskPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class HealthCheck:
    """System health check result"""
    component: str
    status: SystemStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryAction:
    """Automatic recovery action"""
    name: str
    description: str
    action: Callable
    max_retries: int = 3
    cooldown_seconds: int = 60


class AutonomousCore:
    """
    Central autonomous management system.
    
    Features:
    - Health monitoring for all components
    - Automatic error recovery
    - Performance tracking
    - Intelligent scheduling
    - Self-healing capabilities
    """
    
    def __init__(self, db_path: str = "autonomous.db"):
        self.db_path = db_path
        self.status = SystemStatus.HEALTHY
        self.running = False
        self.monitor_thread = None
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.last_recovery: Dict[str, datetime] = {}
        self.health_checks: List[HealthCheck] = []
        
        # Initialize database
        self._init_db()
        
        # Register default recovery actions
        self._register_default_recoveries()
        
        logger.info("AutonomousCore initialized")
    
    def _init_db(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_log (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                component TEXT,
                status TEXT,
                message TEXT,
                metrics TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recovery_log (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                action_name TEXT,
                success INTEGER,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                metric_name TEXT,
                value REAL,
                unit TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_queue (
                id INTEGER PRIMARY KEY,
                created TEXT,
                priority INTEGER,
                task_type TEXT,
                payload TEXT,
                status TEXT,
                started TEXT,
                completed TEXT,
                error TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _register_default_recoveries(self):
        """Register default recovery actions"""
        
        # API Key recovery
        self.register_recovery(
            "api_key_check",
            "Verify and restore API key configuration",
            self._recover_api_key,
            max_retries=2,
            cooldown_seconds=300
        )
        
        # Database recovery
        self.register_recovery(
            "database_repair",
            "Check and repair SQLite databases",
            self._recover_database,
            max_retries=3,
            cooldown_seconds=60
        )
        
        # Memory cleanup
        self.register_recovery(
            "memory_cleanup",
            "Clear caches and free memory",
            self._cleanup_memory,
            max_retries=1,
            cooldown_seconds=300
        )
        
        # Log rotation
        self.register_recovery(
            "log_rotation",
            "Rotate and compress old log files",
            self._rotate_logs,
            max_retries=1,
            cooldown_seconds=3600
        )
    
    def register_recovery(
        self,
        name: str,
        description: str,
        action: Callable,
        max_retries: int = 3,
        cooldown_seconds: int = 60
    ):
        """Register a recovery action"""
        self.recovery_actions[name] = RecoveryAction(
            name=name,
            description=description,
            action=action,
            max_retries=max_retries,
            cooldown_seconds=cooldown_seconds
        )
        logger.debug(f"Registered recovery action: {name}")
    
    # =========================================================================
    # HEALTH MONITORING
    # =========================================================================
    
    def check_health(self) -> Dict[str, HealthCheck]:
        """Perform comprehensive health check"""
        results = {}
        
        # Check OpenAI API
        results["openai_api"] = self._check_openai_api()
        
        # Check database
        results["database"] = self._check_database()
        
        # Check disk space
        results["disk_space"] = self._check_disk_space()
        
        # Check memory
        results["memory"] = self._check_memory()
        
        # Check bot connection
        results["telegram_bot"] = self._check_telegram_bot()
        
        # Aggregate status
        statuses = [r.status for r in results.values()]
        if SystemStatus.CRITICAL in statuses:
            self.status = SystemStatus.CRITICAL
        elif SystemStatus.DEGRADED in statuses:
            self.status = SystemStatus.DEGRADED
        else:
            self.status = SystemStatus.HEALTHY
        
        # Log results
        self._log_health_checks(results)
        
        return results
    
    def _check_openai_api(self) -> HealthCheck:
        """Check OpenAI API connectivity"""
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            
            if not api_key:
                return HealthCheck(
                    component="openai_api",
                    status=SystemStatus.CRITICAL,
                    message="API key not configured"
                )
            
            if not api_key.startswith("sk-"):
                return HealthCheck(
                    component="openai_api",
                    status=SystemStatus.DEGRADED,
                    message="API key format unusual"
                )
            
            # Quick validation (optional - can be expensive)
            # import openai
            # openai.api_key = api_key
            # openai.models.list()
            
            return HealthCheck(
                component="openai_api",
                status=SystemStatus.HEALTHY,
                message="API key configured",
                metrics={"key_prefix": api_key[:15]}
            )
            
        except Exception as e:
            return HealthCheck(
                component="openai_api",
                status=SystemStatus.CRITICAL,
                message=f"API check failed: {str(e)}"
            )
    
    def _check_database(self) -> HealthCheck:
        """Check database health"""
        db_files = ["autonomous.db", "singularity_memory.db", "nexus_business.db"]
        issues = []
        
        for db_file in db_files:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result[0] != "ok":
                        issues.append(f"{db_file}: integrity issue")
                except Exception as e:
                    issues.append(f"{db_file}: {str(e)}")
        
        if issues:
            return HealthCheck(
                component="database",
                status=SystemStatus.DEGRADED,
                message="; ".join(issues)
            )
        
        return HealthCheck(
            component="database",
            status=SystemStatus.HEALTHY,
            message="All databases OK"
        )
    
    def _check_disk_space(self) -> HealthCheck:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024 ** 3)
            used_percent = (used / total) * 100
            
            if free_gb < 1:
                status = SystemStatus.CRITICAL
                message = f"Critical: Only {free_gb:.1f}GB free"
            elif free_gb < 5:
                status = SystemStatus.DEGRADED
                message = f"Warning: Only {free_gb:.1f}GB free"
            else:
                status = SystemStatus.HEALTHY
                message = f"OK: {free_gb:.1f}GB free"
            
            return HealthCheck(
                component="disk_space",
                status=status,
                message=message,
                metrics={"free_gb": free_gb, "used_percent": used_percent}
            )
        except Exception as e:
            return HealthCheck(
                component="disk_space",
                status=SystemStatus.DEGRADED,
                message=f"Check failed: {str(e)}"
            )
    
    def _check_memory(self) -> HealthCheck:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            if memory.percent > 90:
                status = SystemStatus.CRITICAL
            elif memory.percent > 75:
                status = SystemStatus.DEGRADED
            else:
                status = SystemStatus.HEALTHY
            
            return HealthCheck(
                component="memory",
                status=status,
                message=f"Memory usage: {memory.percent:.1f}%",
                metrics={
                    "used_percent": memory.percent,
                    "available_mb": memory.available / (1024 ** 2)
                }
            )
        except ImportError:
            return HealthCheck(
                component="memory",
                status=SystemStatus.DEGRADED,
                message="psutil not installed - cannot check memory"
            )
        except Exception as e:
            return HealthCheck(
                component="memory",
                status=SystemStatus.DEGRADED,
                message=f"Check failed: {str(e)}"
            )
    
    def _check_telegram_bot(self) -> HealthCheck:
        """Check Telegram bot status"""
        try:
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            
            if not bot_token:
                return HealthCheck(
                    component="telegram_bot",
                    status=SystemStatus.DEGRADED,
                    message="Bot token not configured"
                )
            
            return HealthCheck(
                component="telegram_bot",
                status=SystemStatus.HEALTHY,
                message="Bot token configured"
            )
        except Exception as e:
            return HealthCheck(
                component="telegram_bot",
                status=SystemStatus.DEGRADED,
                message=f"Check failed: {str(e)}"
            )
    
    def _log_health_checks(self, results: Dict[str, HealthCheck]):
        """Log health check results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for name, check in results.items():
            cursor.execute("""
                INSERT INTO health_log (timestamp, component, status, message, metrics)
                VALUES (?, ?, ?, ?, ?)
            """, (
                check.timestamp.isoformat(),
                check.component,
                check.status.value,
                check.message,
                json.dumps(check.metrics)
            ))
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # RECOVERY ACTIONS
    # =========================================================================
    
    def _recover_api_key(self) -> bool:
        """Attempt to recover API key configuration"""
        logger.info("Attempting API key recovery...")
        
        # Check .env file
        if os.path.exists(".env"):
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            key = os.getenv("OPENAI_API_KEY", "")
            if key and key.startswith("sk-"):
                logger.info("API key restored from .env")
                return True
        
        # Check backup key
        backup_key = os.getenv("OPENAI_BACKUP_KEY", "")
        if backup_key and backup_key.startswith("sk-"):
            os.environ["OPENAI_API_KEY"] = backup_key
            logger.info("Switched to backup API key")
            return True
        
        logger.error("API key recovery failed - no valid keys found")
        return False
    
    def _recover_database(self) -> bool:
        """Attempt to repair databases"""
        logger.info("Attempting database recovery...")
        
        db_files = ["autonomous.db", "singularity_memory.db", "nexus_business.db"]
        
        for db_file in db_files:
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    # Try vacuum to repair
                    cursor.execute("VACUUM")
                    
                    # Verify integrity
                    cursor.execute("PRAGMA integrity_check")
                    result = cursor.fetchone()
                    
                    conn.commit()
                    conn.close()
                    
                    if result[0] != "ok":
                        logger.warning(f"Database {db_file} has issues: {result[0]}")
                    else:
                        logger.info(f"Database {db_file} repaired")
                        
                except Exception as e:
                    logger.error(f"Database {db_file} recovery failed: {e}")
                    return False
        
        return True
    
    def _cleanup_memory(self) -> bool:
        """Clean up memory and caches"""
        logger.info("Performing memory cleanup...")
        
        import gc
        gc.collect()
        
        # Clear any module-level caches
        # (Add specific cleanup for your modules here)
        
        logger.info("Memory cleanup completed")
        return True
    
    def _rotate_logs(self) -> bool:
        """Rotate old log files"""
        logger.info("Rotating log files...")
        
        log_files = list(Path(".").glob("*.log"))
        
        for log_file in log_files:
            try:
                if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
                    # Rename with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    new_name = f"{log_file.stem}_{timestamp}{log_file.suffix}"
                    log_file.rename(new_name)
                    logger.info(f"Rotated {log_file} to {new_name}")
            except Exception as e:
                logger.warning(f"Could not rotate {log_file}: {e}")
        
        return True
    
    def execute_recovery(self, action_name: str) -> bool:
        """Execute a recovery action with cooldown check"""
        if action_name not in self.recovery_actions:
            logger.error(f"Unknown recovery action: {action_name}")
            return False
        
        action = self.recovery_actions[action_name]
        
        # Check cooldown
        if action_name in self.last_recovery:
            elapsed = (datetime.now() - self.last_recovery[action_name]).seconds
            if elapsed < action.cooldown_seconds:
                logger.info(f"Recovery {action_name} in cooldown ({action.cooldown_seconds - elapsed}s remaining)")
                return False
        
        # Execute with retries
        for attempt in range(action.max_retries):
            try:
                logger.info(f"Executing recovery: {action_name} (attempt {attempt + 1})")
                success = action.action()
                
                # Log result
                self._log_recovery(action_name, success, None)
                self.last_recovery[action_name] = datetime.now()
                
                if success:
                    return True
                    
            except Exception as e:
                logger.error(f"Recovery {action_name} failed: {e}")
                self._log_recovery(action_name, False, str(e))
        
        return False
    
    def _log_recovery(self, action_name: str, success: bool, error: Optional[str]):
        """Log recovery attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO recovery_log (timestamp, action_name, success, error_message)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            action_name,
            1 if success else 0,
            error
        ))
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # TASK SCHEDULING
    # =========================================================================
    
    def add_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> int:
        """Add task to queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO task_queue (created, priority, task_type, payload, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (
            datetime.now().isoformat(),
            priority.value,
            task_type,
            json.dumps(payload)
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added task {task_id}: {task_type} (priority: {priority.name})")
        return task_id
    
    def get_next_task(self) -> Optional[Dict]:
        """Get next task from queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, task_type, payload FROM task_queue
            WHERE status = 'pending'
            ORDER BY priority ASC, created ASC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "task_type": row[1],
                "payload": json.loads(row[2])
            }
        return None
    
    def complete_task(self, task_id: int, error: Optional[str] = None):
        """Mark task as completed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        status = "failed" if error else "completed"
        
        cursor.execute("""
            UPDATE task_queue
            SET status = ?, completed = ?, error = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(), error, task_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Task {task_id} {status}")
    
    # =========================================================================
    # MONITORING LOOP
    # =========================================================================
    
    def start_monitoring(self, interval_seconds: int = 300):
        """Start background monitoring loop"""
        if self.running:
            logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Started monitoring (interval: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Stop monitoring loop"""
        self.running = False
        logger.info("Stopping monitoring...")
    
    def _monitoring_loop(self, interval: int):
        """Background monitoring loop"""
        while self.running:
            try:
                # Run health checks
                results = self.check_health()
                
                # Auto-recover if needed
                for name, check in results.items():
                    if check.status == SystemStatus.CRITICAL:
                        # Find relevant recovery
                        if name == "openai_api":
                            self.execute_recovery("api_key_check")
                        elif name == "database":
                            self.execute_recovery("database_repair")
                        elif name == "memory":
                            self.execute_recovery("memory_cleanup")
                
                # Process tasks
                task = self.get_next_task()
                if task:
                    self._process_task(task)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                traceback.print_exc()
            
            time.sleep(interval)
    
    def _process_task(self, task: Dict):
        """Process a queued task"""
        task_id = task["id"]
        task_type = task["task_type"]
        payload = task["payload"]
        
        logger.info(f"Processing task {task_id}: {task_type}")
        
        # Mark as started
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE task_queue SET status = 'processing', started = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), task_id))
        conn.commit()
        conn.close()
        
        try:
            # Route to handler
            if task_type == "hunt":
                from hunter import execute_real_hunt
                execute_real_hunt(payload.get("keywords", ""))
            elif task_type == "generate":
                from engineer_agent import solve_task
                solve_task(payload.get("task", ""))
            elif task_type == "health_check":
                self.check_health()
            else:
                logger.warning(f"Unknown task type: {task_type}")
            
            self.complete_task(task_id)
            
        except Exception as e:
            self.complete_task(task_id, str(e))
    
    # =========================================================================
    # STATUS REPORTING
    # =========================================================================
    
    def get_status_report(self) -> str:
        """Generate human-readable status report"""
        health = self.check_health()
        
        lines = [
            "",
            "=" * 50,
            "  NEXUS 10 AI AGENCY - SYSTEM STATUS",
            "=" * 50,
            f"  Overall: {self.status.value}",
            f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "-" * 50,
            "  COMPONENTS",
            "-" * 50
        ]
        
        for name, check in health.items():
            icon = "OK" if check.status == SystemStatus.HEALTHY else "!!" if check.status == SystemStatus.DEGRADED else "XX"
            lines.append(f"  [{icon}] {name}: {check.message}")
        
        lines.extend([
            "",
            "-" * 50,
            "  RECOVERY ACTIONS",
            "-" * 50
        ])
        
        for name, action in self.recovery_actions.items():
            last = self.last_recovery.get(name)
            last_str = last.strftime("%H:%M") if last else "Never"
            lines.append(f"  - {name}: Last run: {last_str}")
        
        lines.extend([
            "",
            "=" * 50,
            ""
        ])
        
        return "\n".join(lines)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_core_instance: Optional[AutonomousCore] = None


def get_core() -> AutonomousCore:
    """Get or create the global AutonomousCore instance"""
    global _core_instance
    if _core_instance is None:
        _core_instance = AutonomousCore()
    return _core_instance


def start_autonomous_mode(interval: int = 300):
    """Start autonomous monitoring"""
    core = get_core()
    core.start_monitoring(interval)


def stop_autonomous_mode():
    """Stop autonomous monitoring"""
    if _core_instance:
        _core_instance.stop_monitoring()


def get_system_status() -> str:
    """Get current system status"""
    return get_core().get_status_report()


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  AUTONOMOUS CORE v1.0 - Testing")
    print("=" * 60)
    
    core = AutonomousCore()
    
    # Run health check
    print("\n[Running health checks...]")
    results = core.check_health()
    
    # Print results
    print(core.get_status_report())
    
    # Test task queue
    print("\n[Testing task queue...]")
    task_id = core.add_task("health_check", {}, TaskPriority.LOW)
    print(f"Added task: {task_id}")
    
    task = core.get_next_task()
    print(f"Next task: {task}")
    
    if task:
        core.complete_task(task["id"])
        print("Task completed")



