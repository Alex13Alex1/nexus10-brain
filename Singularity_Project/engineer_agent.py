# -*- coding: utf-8 -*-
"""
ENGINEER AGENT v3.0 - Elite Code Generator with CoT & Self-Healing
===================================================================
- Chain-of-Thought Reasoning (думает перед кодом)
- Multi-File Project Generation
- Self-Healing Code Loops
- Automatic Error Correction
- Production-Ready Output

Author: NEXUS 10 AI Agency
"""

import os
import sys
import time
import json
import re
import openai
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# API keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BACKUP_KEY = os.getenv('OPENAI_BACKUP_KEY', '')
openai.api_key = OPENAI_API_KEY

# Config
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_SELF_HEAL_ATTEMPTS = 3
MIN_QA_SCORE = 75

# =============================================================================
# ELITE SYSTEM PROMPT v3.0 with Chain-of-Thought
# =============================================================================

ENGINEER_SYSTEM_PROMPT_V3 = """You are an ELITE Principal Software Engineer with 20+ years of experience at Google, Meta, and top startups.

## YOUR APPROACH (Chain-of-Thought - ALWAYS FOLLOW):

Before writing ANY code, you MUST:

1. **ANALYZE** (2-3 sentences):
   - What is the core problem?
   - What are the edge cases?
   - What could go wrong?

2. **PLAN** (bullet points):
   - Architecture overview
   - Key components needed
   - Data flow
   - Error handling strategy

3. **IMPLEMENT** (the actual code):
   - Follow ALL best practices below
   - Make it production-ready

## CODE QUALITY STANDARDS (NON-NEGOTIABLE):

### Structure:
```python
# -*- coding: utf-8 -*-
\"\"\"
[Module Name] - [One-line description]
=====================================
[Detailed description in 2-3 sentences]

Author: NEXUS 10 AI Agency
Generated: [timestamp]
Version: 1.0.0
\"\"\"

# === IMPORTS ===
import os
import sys
from typing import Dict, List, Optional
# ... sorted: stdlib first, then third-party

# === CONSTANTS ===
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# === CLASSES & FUNCTIONS ===
class MyClass:
    \"\"\"Docstring with Args, Returns, Raises, Example\"\"\"
    pass

def my_function(param: str) -> dict:
    \"\"\"
    Brief description.
    
    Args:
        param: Description
        
    Returns:
        dict: Description
        
    Raises:
        ValueError: When param is invalid
        
    Example:
        >>> my_function("test")
        {"result": "ok"}
    \"\"\"
    pass

# === MAIN ===
if __name__ == "__main__":
    # Example usage with test
    pass
```

### Security (CRITICAL):
- NEVER hardcode secrets - use os.getenv()
- Sanitize ALL user inputs
- Use parameterized queries for SQL
- Validate file paths to prevent traversal

### Error Handling:
- Wrap external calls in try/except
- Use specific exceptions, not bare except
- Provide meaningful error messages
- Log errors properly

### Performance:
- Use generators for large datasets
- Cache expensive operations
- Avoid N+1 queries
- Profile bottlenecks

### Type Hints:
- ALL functions MUST have type hints
- Use Optional[] for nullable params
- Use Union[] when multiple types accepted

## OUTPUT FORMAT:

Always structure your response as:

### ANALYSIS
[Your thinking about the problem]

### PLAN
[Your architecture/approach]

### CODE
```python
[Complete, runnable code]
```

### REQUIREMENTS
```
package1>=1.0.0
package2>=2.0.0
```

### USAGE
```bash
# How to run the code
```

### TESTS
[Brief test cases or usage examples]

Remember: Your code will be deployed to PRODUCTION. Quality is non-negotiable."""


# =============================================================================
# MULTI-FILE PROJECT PROMPT
# =============================================================================

MULTIFILE_PROMPT = """For complex projects, generate a COMPLETE project structure:

```
project_name/
├── main.py          # Entry point
├── config.py        # Configuration
├── models.py        # Data models (if needed)
├── services.py      # Business logic
├── utils.py         # Helper functions
├── requirements.txt # Dependencies
└── README.md        # Documentation
```

Output each file with clear delimiters:
=== FILE: filename.py ===
[content]
=== END FILE ===
"""


# =============================================================================
# API CALL WITH RETRY
# =============================================================================

def api_call_with_retry(func, *args, **kwargs):
    """Execute API call with automatic retry and key switching"""
    global openai
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
            
        except openai.AuthenticationError as e:
            print(f"[ENGINEER] Auth error (attempt {attempt + 1})")
            if OPENAI_BACKUP_KEY and attempt == 0:
                print("[ENGINEER] Switching to backup key...")
                openai.api_key = OPENAI_BACKUP_KEY
            else:
                last_error = e
                break
                
        except openai.RateLimitError as e:
            wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
            print(f"[ENGINEER] Rate limit, waiting {wait_time}s...")
            time.sleep(wait_time)
            last_error = e
            
        except openai.APIError as e:
            print(f"[ENGINEER] API error: {e}")
            time.sleep(RETRY_DELAY)
            last_error = e
            
        except Exception as e:
            last_error = e
            break
    
    raise last_error if last_error else Exception("Max retries exceeded")


# =============================================================================
# CORE GENERATION FUNCTIONS
# =============================================================================

def solve_task(
    task_description: str, 
    context: str = "",
    complexity: str = "auto",
    enable_cot: bool = True
) -> Dict[str, Any]:
    """
    Generate production-ready code for a task.
    
    Args:
        task_description: What to build
        context: Additional context (client requirements, etc.)
        complexity: "simple", "medium", "complex", or "auto"
        enable_cot: Enable Chain-of-Thought reasoning
        
    Returns:
        dict with: success, code, analysis, plan, requirements, tests
    """
    if not openai.api_key:
        return {"success": False, "error": "API key not configured"}
    
    # Determine complexity
    if complexity == "auto":
        complexity = _estimate_complexity(task_description)
    
    # Build prompt
    system_prompt = ENGINEER_SYSTEM_PROMPT_V3
    if complexity == "complex":
        system_prompt += "\n\n" + MULTIFILE_PROMPT
    
    user_prompt = f"""## TASK
{task_description}

## ADDITIONAL CONTEXT
{context if context else "None provided"}

## COMPLEXITY LEVEL
{complexity.upper()} - {"Generate multiple files if needed" if complexity == "complex" else "Single file solution"}

## REQUIREMENTS
- Code must be immediately runnable
- Include all error handling
- Add proper documentation
- Provide test cases

Generate the solution following the Chain-of-Thought approach."""

    try:
        def make_call():
            return openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower = more consistent
                max_tokens=8000   # Allow for larger outputs
            )
        
        response = api_call_with_retry(make_call)
        full_response = response.choices[0].message.content
        
        # Parse structured response
        result = _parse_cot_response(full_response)
        result["success"] = True
        result["full_response"] = full_response
        result["model"] = "gpt-4o"
        result["complexity"] = complexity
        result["generated_at"] = datetime.now().isoformat()
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "code": "",
            "requirements": []
        }


def generate_multifile_project(
    project_name: str,
    description: str,
    features: List[str]
) -> Dict[str, Any]:
    """
    Generate a complete multi-file project.
    
    Args:
        project_name: Name of the project
        description: What the project does
        features: List of required features
        
    Returns:
        dict with files mapping {filename: content}
    """
    features_str = "\n".join(f"- {f}" for f in features)
    
    prompt = f"""Create a COMPLETE Python project:

## PROJECT: {project_name}

## DESCRIPTION
{description}

## REQUIRED FEATURES
{features_str}

## OUTPUT FORMAT
Generate ALL files needed. Use this exact format:

=== FILE: main.py ===
[complete main.py content]
=== END FILE ===

=== FILE: requirements.txt ===
[dependencies]
=== END FILE ===

Include: main.py, config.py, any module files, requirements.txt, README.md"""

    result = solve_task(prompt, complexity="complex")
    
    if result["success"]:
        files = _extract_files(result["full_response"])
        result["files"] = files
        result["project_name"] = project_name
    
    return result


def self_healing_generate(
    task: str,
    context: str = "",
    max_attempts: int = MAX_SELF_HEAL_ATTEMPTS
) -> Dict[str, Any]:
    """
    Generate code with automatic error correction.
    
    If QA fails, automatically attempts to fix issues.
    
    Args:
        task: Task description
        context: Additional context
        max_attempts: Maximum correction attempts
        
    Returns:
        dict with final code and correction history
    """
    from qa_validator import QAValidator
    
    history = []
    current_code = None
    validator = QAValidator()
    
    for attempt in range(max_attempts):
        print(f"[SELF-HEAL] Attempt {attempt + 1}/{max_attempts}")
        
        if attempt == 0:
            # First generation
            result = solve_task(task, context)
        else:
            # Correction based on previous issues
            correction_prompt = f"""## ORIGINAL TASK
{task}

## PREVIOUS CODE
```python
{current_code}
```

## QA ISSUES FOUND
{chr(10).join(f'- {issue}' for issue in qa_report['issues'])}

## INSTRUCTIONS
Fix ALL the issues above. Output the COMPLETE corrected code.
Do not just describe the changes - provide the full fixed code."""

            result = solve_task(correction_prompt, "Fix the issues from QA")
        
        if not result["success"]:
            history.append({
                "attempt": attempt + 1,
                "status": "generation_failed",
                "error": result.get("error", "Unknown")
            })
            continue
        
        current_code = result["code"]
        qa_report = validator.full_validation(current_code)
        
        history.append({
            "attempt": attempt + 1,
            "qa_score": qa_report["score"],
            "verdict": qa_report["verdict"],
            "issues": qa_report["issues"]
        })
        
        # Success criteria
        if qa_report["score"] >= MIN_QA_SCORE and qa_report["verdict"] != "REJECTED":
            print(f"[SELF-HEAL] Success! Score: {qa_report['score']}")
            return {
                "success": True,
                "code": current_code,
                "final_score": qa_report["score"],
                "attempts": attempt + 1,
                "history": history,
                "qa_report": qa_report
            }
    
    # Max attempts reached
    return {
        "success": False,
        "code": current_code,
        "final_score": qa_report["score"] if 'qa_report' in dir() else 0,
        "attempts": max_attempts,
        "history": history,
        "error": "Max attempts reached without passing QA"
    }


# =============================================================================
# PARSING & EXTRACTION
# =============================================================================

def _estimate_complexity(task: str) -> str:
    """Estimate task complexity from description"""
    task_lower = task.lower()
    
    complex_indicators = [
        "api", "database", "authentication", "multi", "system",
        "platform", "integration", "microservice", "full-stack"
    ]
    medium_indicators = [
        "script", "bot", "monitor", "scraper", "parser",
        "converter", "validator"
    ]
    
    complex_count = sum(1 for ind in complex_indicators if ind in task_lower)
    
    if complex_count >= 2 or len(task) > 500:
        return "complex"
    elif complex_count >= 1 or any(ind in task_lower for ind in medium_indicators):
        return "medium"
    return "simple"


def _parse_cot_response(response: str) -> Dict[str, Any]:
    """Parse Chain-of-Thought structured response"""
    result = {
        "analysis": "",
        "plan": "",
        "code": "",
        "requirements": [],
        "usage": "",
        "tests": ""
    }
    
    # Extract sections
    sections = {
        "analysis": r"###?\s*ANALYSIS\s*\n(.*?)(?=###|\Z)",
        "plan": r"###?\s*PLAN\s*\n(.*?)(?=###|\Z)",
        "code": r"```python\n(.*?)```",
        "requirements": r"###?\s*REQUIREMENTS\s*\n```(?:\w*)?\n?(.*?)```",
        "usage": r"###?\s*USAGE\s*\n(.*?)(?=###|\Z)",
        "tests": r"###?\s*TESTS?\s*\n(.*?)(?=###|\Z)"
    }
    
    for key, pattern in sections.items():
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            result[key] = match.group(1).strip()
    
    # Parse requirements into list
    if result["requirements"]:
        result["requirements"] = [
            line.strip() for line in result["requirements"].split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]
    
    # If no code block found, try to extract any Python code
    if not result["code"]:
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if code_match:
            result["code"] = code_match.group(1).strip()
        else:
            # Last resort: look for import statements
            lines = response.split('\n')
            code_start = -1
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ', '# -*-')):
                    code_start = i
                    break
            if code_start >= 0:
                result["code"] = '\n'.join(lines[code_start:])
    
    return result


def _extract_files(response: str) -> Dict[str, str]:
    """Extract multiple files from response"""
    files = {}
    
    # Pattern: === FILE: filename === content === END FILE ===
    pattern = r'===\s*FILE:\s*([^\s=]+)\s*===\s*\n(.*?)===\s*END FILE\s*==='
    matches = re.findall(pattern, response, re.DOTALL)
    
    for filename, content in matches:
        # Clean up content
        content = content.strip()
        # Remove markdown code blocks if present
        content = re.sub(r'^```\w*\n?', '', content)
        content = re.sub(r'\n?```$', '', content)
        files[filename.strip()] = content.strip()
    
    # Fallback: try to find code blocks with filenames
    if not files:
        blocks = re.findall(r'#\s*(\w+\.py)\n```python\n(.*?)```', response, re.DOTALL)
        for filename, content in blocks:
            files[filename] = content.strip()
    
    return files


# =============================================================================
# QUICK HELPERS
# =============================================================================

def quick_generate(task: str) -> str:
    """Simple interface for backward compatibility"""
    result = solve_task(task)
    return result.get("code", result.get("error", "Generation failed"))


def generate_code(task: str, context: str = "") -> Dict:
    """Alias for solve_task"""
    return solve_task(task, context)


def fix_code(code: str, error_message: str) -> Dict:
    """Fix code based on error message"""
    prompt = f"""Fix this Python code that has an error:

## ERROR
{error_message}

## CODE
```python
{code}
```

Provide the complete fixed code."""
    
    return solve_task(prompt, "Code needs fixing")


def optimize_code(code: str) -> Dict:
    """Optimize existing code for performance"""
    prompt = f"""Optimize this Python code for better performance:

```python
{code}
```

Requirements:
- Keep the same functionality
- Improve speed and memory usage
- Add better error handling if missing
- Add type hints if missing

Provide the complete optimized code."""
    
    return solve_task(prompt, "Performance optimization")


def add_tests(code: str) -> Dict:
    """Generate unit tests for code"""
    prompt = f"""Generate comprehensive unit tests for this code:

```python
{code}
```

Use pytest format. Cover:
- Normal cases
- Edge cases
- Error cases

Output complete test file."""
    
    return solve_task(prompt, "Generate tests")


# =============================================================================
# VALIDATION
# =============================================================================

def validate_code(code: str) -> Dict:
    """Basic validation (use qa_validator for full check)"""
    issues = []
    score = 100
    
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        issues.append(f"Syntax error line {e.lineno}: {e.msg}")
        score -= 50
    
    # Security checks
    dangerous = ['eval(', 'exec(', 'os.system(', '__import__(']
    for d in dangerous:
        if d in code:
            issues.append(f"Security: {d} detected")
            score -= 15
    
    # Hardcoded secrets
    if re.search(r'(password|api_key|secret)\s*=\s*["\'][^"\']{8,}["\']', code, re.I):
        if 'os.getenv' not in code and 'environ' not in code:
            issues.append("Possible hardcoded credentials")
            score -= 20
    
    return {
        "valid": score >= 60,
        "score": max(0, score),
        "issues": issues
    }


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  ENGINEER AGENT v3.0 - Self-Healing Code Generator")
    print("=" * 60)
    
    if not openai.api_key:
        print("\n[ERROR] OPENAI_API_KEY not set")
        sys.exit(1)
    
    # Test self-healing generation
    test_task = """Create a FastAPI REST API for a todo list with:
- CRUD operations (create, read, update, delete)
- SQLite database
- Input validation with Pydantic
- Proper error responses"""
    
    print(f"\n[TASK]: {test_task[:80]}...")
    print("\n[Starting self-healing generation...]\n")
    
    result = self_healing_generate(test_task)
    
    if result["success"]:
        print("\n" + "=" * 60)
        print(f"  SUCCESS in {result['attempts']} attempt(s)")
        print(f"  Final QA Score: {result['final_score']}/100")
        print("=" * 60)
        print("\n[CODE PREVIEW]:")
        print("-" * 40)
        code_preview = result["code"][:1500]
        print(code_preview + ("..." if len(result["code"]) > 1500 else ""))
    else:
        print(f"\n[FAILED]: {result.get('error', 'Unknown error')}")
        print("\n[Correction History]:")
        for h in result.get("history", []):
            print(f"  Attempt {h['attempt']}: Score={h.get('qa_score', 'N/A')}")
