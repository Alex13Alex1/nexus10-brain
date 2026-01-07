"""
🧠 THE NEXUS HIVE v0.95 - Test Script
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from core_engine import run_nexus_hive

# Комплексная мультизадача для тестирования
goal = """Разработай экосистему для автоматизации малого бизнеса: 
складской учет на Python, фронтенд на React и ИИ-аналитик продаж, 
который пишет отчеты в PDF"""

print("🧠 Starting THE NEXUS HIVE v0.95 Test...")
print(f"🎯 Goal: {goal}")
print("-" * 60)

workspace, result = run_nexus_hive(goal)

print(f"\n✅ Test completed!")
print(f"📁 Workspace: {workspace}")














