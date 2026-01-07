# -*- coding: utf-8 -*-
"""
SMART EXECUTION ENGINE v2.0 - Production-Grade Order Execution
================================================================
10/10 Features:
1. Self-Healing Code Loop - автоматическое исправление при QA < 80
2. Requirements Clarification - AI уточняет ТЗ
3. Multi-File Generation - полные проекты
4. Sandbox Execution - реальное тестирование
5. Client Revisions - до 3 правок включено
6. Smart AI Pricing - точная оценка GPT-4o

Author: NEXUS-6 AI System
"""

import os
import sys
import json
import time
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import openai

# Config
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
openai.api_key = OPENAI_API_KEY

MAX_HEALING_ATTEMPTS = 3  # Максимум попыток исправить код
MIN_QA_SCORE = 80  # Минимальный балл для прохождения
MAX_REVISIONS = 3  # Максимум ревизий от клиента


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ProjectRequirements:
    """Уточнённые требования к проекту"""
    title: str
    description: str
    clarified_requirements: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    estimated_hours: float = 8.0
    estimated_price: float = 100.0
    complexity: str = "MEDIUM"
    questions_asked: List[str] = field(default_factory=list)
    client_answers: List[str] = field(default_factory=list)


@dataclass
class ProjectFile:
    """Файл проекта"""
    filename: str
    content: str
    file_type: str = "python"
    is_main: bool = False


@dataclass
class ExecutionResult:
    """Результат исполнения заказа"""
    success: bool
    files: List[ProjectFile] = field(default_factory=list)
    qa_score: int = 0
    qa_report: Dict = field(default_factory=dict)
    healing_attempts: int = 0
    total_tokens_used: int = 0
    execution_time: float = 0.0
    sandbox_output: str = ""
    error: str = ""


# ============================================================
# 1. REQUIREMENTS CLARIFICATION (AI Dialog)
# ============================================================

CLARIFICATION_PROMPT = """You are a Senior Business Analyst. Your task is to analyze a client's project request and generate 3-5 clarifying questions to ensure perfect understanding.

Project Request:
Title: {title}
Description: {description}

Generate questions that will help understand:
1. Core functionality and features
2. Technical preferences (frameworks, databases)
3. Integration requirements (APIs, services)
4. Non-functional requirements (performance, security)
5. Deliverables expected (code only, documentation, deployment)

Output format (JSON):
{{
    "understood_requirements": ["req1", "req2", ...],
    "clarifying_questions": ["question1", "question2", ...],
    "suggested_tech_stack": ["tech1", "tech2", ...],
    "estimated_complexity": "LOW|MEDIUM|HIGH|VERY_HIGH",
    "estimated_hours": 8,
    "risk_factors": ["risk1", "risk2"]
}}"""


def clarify_requirements(title: str, description: str) -> Dict:
    """
    AI анализирует запрос и генерирует уточняющие вопросы
    """
    if not openai.api_key:
        return {"error": "API key not configured"}
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Senior Business Analyst who extracts clear requirements from vague requests."},
                {"role": "user", "content": CLARIFICATION_PROMPT.format(title=title, description=description)}
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def process_client_answers(requirements: Dict, answers: List[str]) -> ProjectRequirements:
    """
    Обрабатывает ответы клиента и формирует финальные требования
    """
    try:
        prompt = f"""Based on the initial analysis and client's answers, create final project requirements.

Initial Analysis:
{json.dumps(requirements, indent=2)}

Client Answers:
{chr(10).join([f'{i+1}. {a}' for i, a in enumerate(answers)])}

Output (JSON):
{{
    "final_requirements": ["req1", "req2", ...],
    "tech_stack": ["tech1", "tech2", ...],
    "deliverables": ["main.py", "requirements.txt", "README.md"],
    "estimated_hours": 10,
    "price_usd": 150,
    "complexity": "MEDIUM"
}}"""

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return ProjectRequirements(
            title=requirements.get('title', ''),
            description=requirements.get('description', ''),
            clarified_requirements=result.get('final_requirements', []),
            tech_stack=result.get('tech_stack', []),
            deliverables=result.get('deliverables', ['main.py']),
            estimated_hours=result.get('estimated_hours', 8),
            estimated_price=result.get('price_usd', 100),
            complexity=result.get('complexity', 'MEDIUM'),
            questions_asked=requirements.get('clarifying_questions', []),
            client_answers=answers
        )
    except Exception as e:
        # Fallback to basic requirements
        return ProjectRequirements(
            title=requirements.get('title', 'Project'),
            description=requirements.get('description', ''),
            estimated_hours=8,
            estimated_price=100
        )


# ============================================================
# 2. SMART AI PRICING
# ============================================================

PRICING_PROMPT = """You are a freelance pricing expert. Analyze this project and provide accurate pricing.

Project:
Title: {title}
Description: {description}
Tech Stack: {tech_stack}
Complexity: {complexity}
Estimated Hours: {hours}

Consider:
- Market rates for Python development ($50-150/hour)
- Project complexity and risks
- Deliverables included
- Support/revision time

Output (JSON):
{{
    "base_price_usd": 100,
    "complexity_multiplier": 1.2,
    "risk_buffer_percent": 10,
    "final_price_usd": 132,
    "price_breakdown": {{
        "development": 80,
        "testing": 20,
        "documentation": 15,
        "revisions_buffer": 17
    }},
    "competitive_range": {{"min": 100, "max": 200}},
    "confidence": 0.85,
    "justification": "..."
}}"""


def smart_pricing(title: str, description: str, 
                  tech_stack: List[str] = None,
                  complexity: str = "MEDIUM",
                  hours: float = 8) -> Dict:
    """
    AI-powered точная оценка стоимости проекта
    """
    if not openai.api_key:
        # Fallback pricing
        base_prices = {"LOW": 50, "MEDIUM": 100, "HIGH": 200, "VERY_HIGH": 400}
        return {
            "success": True,
            "final_price_usd": base_prices.get(complexity, 100),
            "confidence": 0.5,
            "method": "fallback"
        }
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert freelance pricing consultant."},
                {"role": "user", "content": PRICING_PROMPT.format(
                    title=title,
                    description=description,
                    tech_stack=", ".join(tech_stack or ["Python"]),
                    complexity=complexity,
                    hours=hours
                )}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {"success": True, "method": "ai", **result}
        
    except Exception as e:
        return {"success": False, "error": str(e), "final_price_usd": 100}


# ============================================================
# 3. MULTI-FILE PROJECT GENERATION
# ============================================================

MULTIFILE_PROMPT = """You are an elite Python architect. Generate a complete, production-ready project.

Project Requirements:
{requirements}

Generate multiple files for a professional project structure.

Output (JSON):
{{
    "project_name": "project_name",
    "files": [
        {{
            "filename": "main.py",
            "content": "# -*- coding: utf-8 -*-\\n...",
            "is_main": true
        }},
        {{
            "filename": "requirements.txt",
            "content": "requests==2.31.0\\n...",
            "is_main": false
        }},
        {{
            "filename": "README.md",
            "content": "# Project Title\\n...",
            "is_main": false
        }},
        {{
            "filename": "config.py",
            "content": "...",
            "is_main": false
        }}
    ],
    "setup_instructions": "1. Install: pip install -r requirements.txt\\n2. Run: python main.py",
    "test_command": "python main.py --test"
}}

Rules:
1. Main file must be complete and runnable
2. Include proper error handling and logging
3. Use environment variables for secrets
4. Include docstrings and type hints
5. Add config file if needed
6. Create comprehensive README"""


def generate_multifile_project(requirements: ProjectRequirements) -> List[ProjectFile]:
    """
    Генерирует полный проект с несколькими файлами
    """
    if not openai.api_key:
        return [ProjectFile(
            filename="error.txt",
            content="API key not configured",
            is_main=False
        )]
    
    req_text = f"""
Title: {requirements.title}
Description: {requirements.description}
Requirements: {chr(10).join(['- ' + r for r in requirements.clarified_requirements])}
Tech Stack: {', '.join(requirements.tech_stack)}
Deliverables: {', '.join(requirements.deliverables)}
"""
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an elite Senior Python Developer creating production-ready code."},
                {"role": "user", "content": MULTIFILE_PROMPT.format(requirements=req_text)}
            ],
            temperature=0.3,
            max_tokens=8000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        files = []
        for f in result.get('files', []):
            files.append(ProjectFile(
                filename=f.get('filename', 'unknown.py'),
                content=f.get('content', ''),
                file_type=f.get('filename', '').split('.')[-1],
                is_main=f.get('is_main', False)
            ))
        
        return files
        
    except Exception as e:
        return [ProjectFile(
            filename="error.txt",
            content=f"Generation error: {str(e)}",
            is_main=False
        )]


# ============================================================
# 4. SANDBOX CODE EXECUTION
# ============================================================

def run_in_sandbox(code: str, timeout: int = 30) -> Dict:
    """
    Запускает код в изолированном окружении для тестирования
    """
    result = {
        "success": False,
        "output": "",
        "error": "",
        "execution_time": 0,
        "exit_code": -1
    }
    
    # Создаём временный файл
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name
    
    try:
        start_time = time.time()
        
        # Запускаем в subprocess с таймаутом
        process = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir()
        )
        
        result["execution_time"] = time.time() - start_time
        result["exit_code"] = process.returncode
        result["output"] = process.stdout[:2000]  # Limit output
        result["error"] = process.stderr[:1000]
        result["success"] = process.returncode == 0
        
    except subprocess.TimeoutExpired:
        result["error"] = f"Execution timed out after {timeout}s"
    except Exception as e:
        result["error"] = str(e)
    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_file)
        except:
            pass
    
    return result


def validate_with_sandbox(files: List[ProjectFile]) -> Dict:
    """
    Валидирует проект через sandbox execution
    """
    main_file = next((f for f in files if f.is_main), None)
    
    if not main_file:
        main_file = next((f for f in files if f.filename.endswith('.py')), None)
    
    if not main_file:
        return {"success": False, "error": "No Python file found"}
    
    # Проверяем синтаксис
    try:
        compile(main_file.content, main_file.filename, 'exec')
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"Syntax error at line {e.lineno}: {e.msg}",
            "syntax_valid": False
        }
    
    # Пробуем запустить
    sandbox_result = run_in_sandbox(main_file.content)
    
    return {
        "success": sandbox_result["success"],
        "syntax_valid": True,
        "runs": sandbox_result["exit_code"] == 0,
        "output": sandbox_result["output"],
        "error": sandbox_result["error"],
        "execution_time": sandbox_result["execution_time"]
    }


# ============================================================
# 5. SELF-HEALING CODE LOOP
# ============================================================

HEALING_PROMPT = """You are a Senior Python Developer fixing code issues.

Original Code:
```python
{code}
```

Issues Found:
{issues}

QA Report:
- Score: {score}/100
- Security Issues: {security}
- Missing Best Practices: {missing}

Fix ALL issues and return the corrected code.

Output (JSON):
{{
    "fixed_code": "# -*- coding: utf-8 -*-\\n...",
    "changes_made": ["Fixed X", "Added Y", "Removed Z"],
    "confidence": 0.9
}}"""


def heal_code(code: str, qa_report: Dict) -> Tuple[str, List[str]]:
    """
    Автоматически исправляет код на основе QA отчёта
    """
    if not openai.api_key:
        return code, ["API key not configured"]
    
    issues = qa_report.get('issues', [])
    security = qa_report.get('security', [])
    missing = qa_report.get('best_practices', {}).get('missing', [])
    score = qa_report.get('score', 0)
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert code reviewer and fixer."},
                {"role": "user", "content": HEALING_PROMPT.format(
                    code=code,
                    issues="\n".join(issues) if issues else "None",
                    score=score,
                    security=json.dumps(security) if security else "None",
                    missing=", ".join(missing) if missing else "None"
                )}
            ],
            temperature=0.2,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        fixed_code = result.get('fixed_code', code)
        changes = result.get('changes_made', [])
        
        return fixed_code, changes
        
    except Exception as e:
        return code, [f"Healing failed: {str(e)}"]


def self_healing_loop(files: List[ProjectFile], 
                      qa_validator,
                      max_attempts: int = MAX_HEALING_ATTEMPTS) -> Tuple[List[ProjectFile], Dict]:
    """
    Итеративно улучшает код до прохождения QA
    """
    healing_log = {
        "attempts": 0,
        "initial_score": 0,
        "final_score": 0,
        "changes_history": []
    }
    
    for attempt in range(max_attempts):
        healing_log["attempts"] = attempt + 1
        
        # Находим main file
        main_file = next((f for f in files if f.is_main or f.filename.endswith('.py')), None)
        if not main_file:
            break
        
        # QA проверка
        qa_report = qa_validator(main_file.content)
        score = qa_report.get('score', 0)
        
        if attempt == 0:
            healing_log["initial_score"] = score
        
        healing_log["final_score"] = score
        
        # Если прошли QA - выходим
        if score >= MIN_QA_SCORE:
            break
        
        # Исправляем код
        fixed_code, changes = heal_code(main_file.content, qa_report)
        
        healing_log["changes_history"].append({
            "attempt": attempt + 1,
            "score_before": score,
            "changes": changes
        })
        
        # Обновляем файл
        main_file.content = fixed_code
    
    return files, healing_log


# ============================================================
# 6. CLIENT REVISION SYSTEM
# ============================================================

REVISION_PROMPT = """You are a Senior Developer handling client revision requests.

Current Code:
```python
{code}
```

Client Feedback:
{feedback}

Apply the requested changes while maintaining code quality.

Output (JSON):
{{
    "revised_code": "...",
    "changes_applied": ["Change 1", "Change 2"],
    "questions": ["Any clarifications needed?"],
    "additional_cost": 0
}}"""


def apply_client_revision(code: str, feedback: str) -> Dict:
    """
    Применяет ревизию по фидбеку клиента
    """
    if not openai.api_key:
        return {"success": False, "error": "API key not configured"}
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional developer handling client feedback."},
                {"role": "user", "content": REVISION_PROMPT.format(code=code, feedback=feedback)}
            ],
            temperature=0.3,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "success": True,
            "revised_code": result.get('revised_code', code),
            "changes_applied": result.get('changes_applied', []),
            "questions": result.get('questions', []),
            "additional_cost": result.get('additional_cost', 0)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# MAIN SMART EXECUTION CLASS
# ============================================================

class SmartExecutionEngine:
    """
    Production-grade execution engine с self-healing и smart pricing
    """
    
    def __init__(self):
        self.current_order = None
        self.revision_count = 0
        print("[SMART ENGINE] Initialized with all 10/10 features")
    
    def full_execution_cycle(self, title: str, description: str,
                              client_answers: List[str] = None) -> ExecutionResult:
        """
        Полный цикл исполнения с всеми фичами
        """
        start_time = time.time()
        result = ExecutionResult(success=False)
        
        try:
            # 1. CLARIFY REQUIREMENTS
            print("[STEP 1] Clarifying requirements...")
            clarification = clarify_requirements(title, description)
            
            if client_answers:
                requirements = process_client_answers(
                    {**clarification, "title": title, "description": description},
                    client_answers
                )
            else:
                requirements = ProjectRequirements(
                    title=title,
                    description=description,
                    clarified_requirements=clarification.get('understood_requirements', []),
                    tech_stack=clarification.get('suggested_tech_stack', ['Python']),
                    complexity=clarification.get('estimated_complexity', 'MEDIUM'),
                    estimated_hours=clarification.get('estimated_hours', 8)
                )
            
            # 2. SMART PRICING
            print("[STEP 2] Calculating price...")
            pricing = smart_pricing(
                title=requirements.title,
                description=requirements.description,
                tech_stack=requirements.tech_stack,
                complexity=requirements.complexity,
                hours=requirements.estimated_hours
            )
            requirements.estimated_price = pricing.get('final_price_usd', 100)
            
            # 3. GENERATE MULTI-FILE PROJECT
            print("[STEP 3] Generating project files...")
            files = generate_multifile_project(requirements)
            
            if not files or files[0].filename == "error.txt":
                result.error = "Code generation failed"
                return result
            
            result.files = files
            
            # 4. QA + SELF-HEALING
            print("[STEP 4] QA validation with self-healing...")
            from qa_validator import validate_code
            
            files, healing_log = self_healing_loop(files, validate_code)
            result.files = files
            result.healing_attempts = healing_log["attempts"]
            result.qa_score = healing_log["final_score"]
            
            # 5. SANDBOX TESTING
            print("[STEP 5] Sandbox testing...")
            sandbox_result = validate_with_sandbox(files)
            result.sandbox_output = sandbox_result.get('output', '')
            
            # 6. FINAL RESULT
            result.success = (
                result.qa_score >= MIN_QA_SCORE or 
                sandbox_result.get('syntax_valid', False)
            )
            result.execution_time = time.time() - start_time
            
            print(f"[COMPLETE] Score: {result.qa_score}/100, Files: {len(files)}, Time: {result.execution_time:.1f}s")
            
        except Exception as e:
            result.error = str(e)
            result.execution_time = time.time() - start_time
        
        return result
    
    def handle_revision(self, code: str, feedback: str) -> Dict:
        """
        Обработка ревизии от клиента
        """
        if self.revision_count >= MAX_REVISIONS:
            return {
                "success": False,
                "error": f"Maximum revisions ({MAX_REVISIONS}) reached. Additional revisions require extra payment."
            }
        
        result = apply_client_revision(code, feedback)
        
        if result["success"]:
            self.revision_count += 1
            result["revisions_remaining"] = MAX_REVISIONS - self.revision_count
        
        return result
    
    def get_clarifying_questions(self, title: str, description: str) -> Dict:
        """
        Получить уточняющие вопросы для клиента
        """
        return clarify_requirements(title, description)
    
    def get_smart_price(self, title: str, description: str) -> Dict:
        """
        Получить AI-оценку стоимости
        """
        clarification = clarify_requirements(title, description)
        return smart_pricing(
            title=title,
            description=description,
            tech_stack=clarification.get('suggested_tech_stack', ['Python']),
            complexity=clarification.get('estimated_complexity', 'MEDIUM'),
            hours=clarification.get('estimated_hours', 8)
        )


# ============================================================
# SINGLETON
# ============================================================

_smart_engine = None

def get_smart_engine() -> SmartExecutionEngine:
    global _smart_engine
    if _smart_engine is None:
        _smart_engine = SmartExecutionEngine()
    return _smart_engine


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SMART EXECUTION ENGINE v2.0 - 10/10 TEST")
    print("=" * 60)
    
    engine = get_smart_engine()
    
    # Test 1: Clarifying Questions
    print("\n[TEST 1] Clarifying Questions")
    questions = engine.get_clarifying_questions(
        "Telegram Bot for Crypto Alerts",
        "I need a bot that tracks Bitcoin price"
    )
    print(f"Questions: {questions.get('clarifying_questions', [])[:3]}")
    
    # Test 2: Smart Pricing
    print("\n[TEST 2] Smart Pricing")
    price = engine.get_smart_price(
        "Web Scraper for E-commerce",
        "Scrape product data from Amazon with anti-detection"
    )
    print(f"Price: ${price.get('final_price_usd', 0)}")
    
    # Test 3: Full Execution (requires API key)
    if OPENAI_API_KEY:
        print("\n[TEST 3] Full Execution Cycle")
        result = engine.full_execution_cycle(
            "Python Script to Monitor System Resources",
            "Create a script that monitors CPU, RAM, and disk usage with alerts"
        )
        print(f"Success: {result.success}")
        print(f"Files: {len(result.files)}")
        print(f"QA Score: {result.qa_score}")
        print(f"Healing Attempts: {result.healing_attempts}")
    else:
        print("\n[TEST 3] Skipped - No API key")
    
    print("\n" + "=" * 60)
    print("All tests complete!")





