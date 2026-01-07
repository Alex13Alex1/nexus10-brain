# -*- coding: utf-8 -*-
"""
NEXUS 10 AI AGENCY - Self-Healing Code System
==============================================
Автоматическое исправление кода при отклонении QA.
Многопроходная генерация до достижения качества.

Author: Nexus 10 AI Agency
"""

import os
import openai
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY', '')

# === CONFIG ===
MAX_HEALING_ATTEMPTS = 3
MIN_ACCEPTABLE_SCORE = 75
HEALING_TEMPERATURE = 0.4  # Slightly higher for creative fixes


class CodeHealer:
    """
    Автоматически исправляет код на основе QA отчётов.
    """
    
    def __init__(self):
        self.healing_history: List[Dict] = []
    
    def heal_code(self, original_code: str, qa_report: Dict, 
                  task_description: str = "") -> Dict:
        """
        Исправить код на основе QA отчёта.
        
        Args:
            original_code: Исходный код
            qa_report: Отчёт от QA {"score": int, "issues": list}
            task_description: Описание задачи для контекста
        
        Returns:
            {"success": bool, "code": str, "attempts": int, "final_score": int}
        """
        current_code = original_code
        current_score = qa_report.get("score", 0)
        issues = qa_report.get("issues", [])
        
        for attempt in range(1, MAX_HEALING_ATTEMPTS + 1):
            print(f"[HEALER] Attempt {attempt}/{MAX_HEALING_ATTEMPTS}")
            print(f"         Current score: {current_score}/100")
            
            if current_score >= MIN_ACCEPTABLE_SCORE:
                print(f"[HEALER] Score acceptable ({current_score} >= {MIN_ACCEPTABLE_SCORE})")
                return {
                    "success": True,
                    "code": current_code,
                    "attempts": attempt - 1,
                    "final_score": current_score,
                    "history": self.healing_history
                }
            
            # Generate fix
            fix_result = self._generate_fix(current_code, issues, task_description)
            
            if not fix_result["success"]:
                print(f"[HEALER] Fix generation failed: {fix_result.get('error')}")
                continue
            
            fixed_code = fix_result["code"]
            
            # Validate fixed code
            from engineer_agent import validate_code
            new_validation = validate_code(fixed_code)
            
            # Record history
            self.healing_history.append({
                "attempt": attempt,
                "old_score": current_score,
                "new_score": new_validation["score"],
                "issues_fixed": issues,
                "new_issues": new_validation["issues"],
                "timestamp": datetime.now().isoformat()
            })
            
            current_code = fixed_code
            current_score = new_validation["score"]
            issues = new_validation["issues"]
            
            print(f"[HEALER] After fix: {current_score}/100")
        
        # Max attempts reached
        final_success = current_score >= MIN_ACCEPTABLE_SCORE
        return {
            "success": final_success,
            "code": current_code,
            "attempts": MAX_HEALING_ATTEMPTS,
            "final_score": current_score,
            "history": self.healing_history,
            "message": "Max attempts reached" if not final_success else "Fixed after max attempts"
        }
    
    def _generate_fix(self, code: str, issues: List[str], 
                      task_description: str) -> Dict:
        """Generate code fix using AI"""
        
        if not openai.api_key:
            return {"success": False, "error": "No API key"}
        
        issues_text = "\n".join([f"- {issue}" for issue in issues])
        
        prompt = f"""You are a code fixer. Fix the following Python code based on the issues identified.

ORIGINAL TASK: {task_description}

CURRENT CODE:
```python
{code}
```

ISSUES TO FIX:
{issues_text}

REQUIREMENTS:
1. Fix ALL listed issues
2. Keep the original functionality intact
3. Maintain code style and structure
4. Add proper error handling
5. Ensure code runs without errors

Return ONLY the fixed Python code, no explanations."""

        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert Python developer fixing code issues."},
                    {"role": "user", "content": prompt}
                ],
                temperature=HEALING_TEMPERATURE,
                max_tokens=4000
            )
            
            fixed_code = response.choices[0].message.content
            
            # Extract code from markdown if present
            if "```python" in fixed_code:
                import re
                matches = re.findall(r'```python\n(.*?)```', fixed_code, re.DOTALL)
                if matches:
                    fixed_code = matches[0]
            elif "```" in fixed_code:
                import re
                matches = re.findall(r'```\n?(.*?)```', fixed_code, re.DOTALL)
                if matches:
                    fixed_code = matches[0]
            
            return {
                "success": True,
                "code": fixed_code.strip()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def auto_heal_and_validate(code: str, task: str) -> Dict:
    """
    Автоматически валидирует и лечит код.
    Возвращает финальный код если успешно.
    """
    from engineer_agent import validate_code
    
    # Initial validation
    initial_validation = validate_code(code)
    
    if initial_validation["score"] >= MIN_ACCEPTABLE_SCORE:
        return {
            "success": True,
            "code": code,
            "score": initial_validation["score"],
            "healed": False
        }
    
    # Need healing
    healer = CodeHealer()
    result = healer.heal_code(code, initial_validation, task)
    
    return {
        "success": result["success"],
        "code": result["code"],
        "score": result["final_score"],
        "healed": True,
        "attempts": result["attempts"]
    }


# === FULL PIPELINE WITH SELF-HEALING ===

def generate_and_heal(task_description: str) -> Dict:
    """
    Полный pipeline: генерация + QA + self-healing.
    
    Returns:
        {"success": bool, "code": str, "score": int, "healed": bool}
    """
    from engineer_agent import solve_task
    
    # Step 1: Generate
    print("[PIPELINE] Step 1: Generating code...")
    gen_result = solve_task(task_description)
    
    if not gen_result["success"]:
        return {
            "success": False,
            "code": "",
            "score": 0,
            "error": gen_result.get("explanation", "Generation failed")
        }
    
    code = gen_result["code"]
    
    # Step 2: Validate + Heal
    print("[PIPELINE] Step 2: Validating and healing if needed...")
    heal_result = auto_heal_and_validate(code, task_description)
    
    return {
        "success": heal_result["success"],
        "code": heal_result["code"],
        "score": heal_result["score"],
        "healed": heal_result.get("healed", False),
        "attempts": heal_result.get("attempts", 0),
        "requirements": gen_result.get("requirements", [])
    }


# === AGENT COMMUNICATION BRIDGE ===

class AgentCommunicator:
    """
    Обеспечивает коммуникацию между агентами.
    Позволяет QA отправить код обратно Doer для исправления.
    """
    
    def __init__(self):
        self.message_queue: List[Dict] = []
        self.feedback_log: List[Dict] = []
    
    def send_to_doer(self, from_agent: str, message: str, code: str = "", 
                     issues: List[str] = None):
        """QA/Architect отправляет feedback Doer'у"""
        msg = {
            "from": from_agent,
            "to": "doer",
            "type": "revision_request",
            "message": message,
            "code": code,
            "issues": issues or [],
            "timestamp": datetime.now().isoformat()
        }
        self.message_queue.append(msg)
        self.feedback_log.append(msg)
        return msg
    
    def send_to_qa(self, from_agent: str, code: str, context: str = ""):
        """Doer отправляет код на проверку QA"""
        msg = {
            "from": from_agent,
            "to": "qa",
            "type": "review_request",
            "code": code,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self.message_queue.append(msg)
        return msg
    
    def send_to_client(self, message: str, code: str = "", 
                       invoice: bool = False):
        """Отправка клиенту (через Collector)"""
        msg = {
            "to": "client",
            "type": "delivery" if code else "message",
            "message": message,
            "code": code,
            "invoice_attached": invoice,
            "timestamp": datetime.now().isoformat()
        }
        self.message_queue.append(msg)
        return msg
    
    def get_pending_messages(self, for_agent: str) -> List[Dict]:
        """Получить сообщения для конкретного агента"""
        pending = [m for m in self.message_queue if m.get("to") == for_agent]
        # Clear processed
        self.message_queue = [m for m in self.message_queue if m.get("to") != for_agent]
        return pending
    
    def get_feedback_log(self) -> List[Dict]:
        """История всех feedback сообщений"""
        return self.feedback_log


# Singleton communicator
_communicator = None

def get_communicator() -> AgentCommunicator:
    global _communicator
    if _communicator is None:
        _communicator = AgentCommunicator()
    return _communicator


# === TEST ===

if __name__ == "__main__":
    print("=" * 60)
    print("NEXUS 10 - Self-Healing Code System Test")
    print("=" * 60)
    
    # Test code with issues
    bad_code = '''
def hello():
    print("Hello)  # Missing quote
    password = "secret123"  # Hardcoded!
    
hello()
'''
    
    print("\n[TEST 1] Validating bad code:")
    from engineer_agent import validate_code
    result = validate_code(bad_code)
    print(f"Score: {result['score']}/100")
    print(f"Issues: {result['issues']}")
    
    print("\n[TEST 2] Full pipeline with simple task:")
    if openai.api_key:
        result = generate_and_heal("Create a function that adds two numbers")
        print(f"Success: {result['success']}")
        print(f"Score: {result['score']}/100")
        print(f"Healed: {result.get('healed', False)}")
        if result["code"]:
            print(f"Code preview: {result['code'][:200]}...")
    else:
        print("Skipped - no API key")
    
    print("\n[TEST 3] Agent Communication:")
    comm = get_communicator()
    comm.send_to_doer("qa", "Fix the security issue", bad_code, ["Hardcoded password"])
    pending = comm.get_pending_messages("doer")
    print(f"Messages for Doer: {len(pending)}")
    if pending:
        print(f"First message type: {pending[0]['type']}")
    
    print("\n" + "=" * 60)


