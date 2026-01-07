# -*- coding: utf-8 -*-
"""
QA VALIDATOR v3.0 - Elite Code Quality Assurance
=================================================
- Static Analysis (AST parsing)
- Security Scanning
- Runtime Testing in Sandbox
- Code Smell Detection
- Performance Analysis
- Auto-Fix Suggestions

Author: NEXUS 10 AI Agency
"""

import ast
import sys
import re
import io
import os
import time
import tempfile
import subprocess
import traceback
from typing import Dict, List, Tuple, Any, Optional
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Issue:
    severity: Severity
    category: str
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None


class QAValidator:
    """
    Elite code validator with comprehensive checks.
    
    Usage:
        validator = QAValidator()
        report = validator.full_validation(code)
        print(validator.format_report(report))
    """
    
    # Security patterns - CRITICAL
    SECURITY_PATTERNS = [
        (r'\beval\s*\(', "eval() allows arbitrary code execution", "Use ast.literal_eval() for safe parsing"),
        (r'\bexec\s*\(', "exec() allows arbitrary code execution", "Refactor to avoid dynamic execution"),
        (r'\b__import__\s*\(', "__import__() can load malicious modules", "Use explicit imports"),
        (r'subprocess\.[^(]*\([^)]*shell\s*=\s*True', "shell=True enables command injection", "Use shell=False with list args"),
        (r'os\.system\s*\(', "os.system() is vulnerable to injection", "Use subprocess.run() instead"),
        (r'pickle\.loads?\s*\(', "pickle is unsafe for untrusted data", "Use json for serialization"),
        (r'yaml\.load\s*\([^)]*(?!Loader)', "yaml.load() can execute code", "Use yaml.safe_load()"),
        (r'input\s*\([^)]*\)\s*$', "Raw input() without validation", "Validate and sanitize input"),
        (r'(password|api_key|secret|token)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded credentials detected", "Use os.getenv()"),
        (r'verify\s*=\s*False', "SSL verification disabled", "Enable SSL verification in production"),
    ]
    
    # Code smells - MEDIUM
    CODE_SMELLS = [
        (r'except\s*:', "Bare except catches everything including KeyboardInterrupt", "Catch specific exceptions"),
        (r'except\s+Exception\s*:', "Catching Exception is too broad", "Catch specific exception types"),
        (r'\.append\([^)]+\)\s*$.*for\s+', "List append in loop can be slow", "Use list comprehension"),
        (r'global\s+\w+', "Global variables reduce modularity", "Pass as function parameters"),
        (r'from\s+\w+\s+import\s+\*', "Wildcard imports pollute namespace", "Import specific names"),
        (r'time\.sleep\s*\(\s*\d{2,}\s*\)', "Long sleep may indicate design issue", "Consider async/event-driven"),
        (r'print\s*\([^)]*\)\s*$', "Print statements in production code", "Use logging module"),
        (r'#\s*TODO|#\s*FIXME|#\s*XXX|#\s*HACK', "Unresolved TODO/FIXME comment", "Address before deployment"),
    ]
    
    # Required patterns - INFO
    GOOD_PRACTICES = [
        (r'try\s*:', "Error handling present", 10),
        (r'except\s+\w+Error', "Specific exception handling", 5),
        (r'"""[\s\S]{20,}?"""', "Docstrings present", 10),
        (r'#.*\S', "Comments present", 3),
        (r'if\s+__name__\s*==\s*["\']__main__["\']', "Main guard present", 5),
        (r'import\s+logging|from\s+logging', "Logging module used", 5),
        (r'def\s+\w+\s*\([^)]*\)\s*->', "Type hints present", 8),
        (r'raise\s+\w+Error', "Proper exception raising", 5),
        (r'with\s+open\s*\(', "Context manager for files", 5),
        (r'@\w+', "Decorators used", 3),
        (r'assert\s+', "Assertions for validation", 3),
        (r'from\s+typing\s+import', "Type annotations imported", 5),
    ]
    
    def __init__(self, timeout: int = 5):
        """Initialize validator with execution timeout"""
        self.timeout = timeout
        self.issues: List[Issue] = []
    
    def validate_syntax(self, code: str) -> Tuple[bool, str, Optional[int]]:
        """
        Check Python syntax validity.
        
        Returns:
            (is_valid, message, error_line)
        """
        try:
            ast.parse(code)
            return True, "Syntax OK", None
        except SyntaxError as e:
            return False, f"Line {e.lineno}: {e.msg}", e.lineno
    
    def analyze_ast(self, code: str) -> Dict[str, Any]:
        """
        Deep AST analysis for code metrics.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"error": "Cannot parse - syntax error"}
        
        metrics = {
            "functions": [],
            "classes": [],
            "imports": [],
            "global_vars": [],
            "complexity": 0,
            "nested_depth": 0
        }
        
        class Analyzer(ast.NodeVisitor):
            def __init__(self):
                self.depth = 0
                self.max_depth = 0
            
            def visit_FunctionDef(self, node):
                metrics["functions"].append({
                    "name": node.name,
                    "args": len(node.args.args),
                    "line": node.lineno,
                    "has_docstring": ast.get_docstring(node) is not None,
                    "has_return_type": node.returns is not None
                })
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
                self.generic_visit(node)
                self.depth -= 1
            
            def visit_AsyncFunctionDef(self, node):
                self.visit_FunctionDef(node)
            
            def visit_ClassDef(self, node):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                metrics["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": len(methods),
                    "has_docstring": ast.get_docstring(node) is not None
                })
                self.generic_visit(node)
            
            def visit_Import(self, node):
                for alias in node.names:
                    metrics["imports"].append(alias.name.split('.')[0])
            
            def visit_ImportFrom(self, node):
                if node.module:
                    metrics["imports"].append(node.module.split('.')[0])
            
            def visit_If(self, node):
                metrics["complexity"] += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                metrics["complexity"] += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                metrics["complexity"] += 1
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                metrics["complexity"] += 1
                self.generic_visit(node)
        
        analyzer = Analyzer()
        analyzer.visit(tree)
        metrics["nested_depth"] = analyzer.max_depth
        metrics["imports"] = list(set(metrics["imports"]))
        
        return metrics
    
    def security_scan(self, code: str) -> List[Issue]:
        """Scan for security vulnerabilities"""
        issues = []
        lines = code.split('\n')
        
        for pattern, message, suggestion in self.SECURITY_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(Issue(
                        severity=Severity.CRITICAL if "injection" in message.lower() or "arbitrary" in message.lower() else Severity.HIGH,
                        category="SECURITY",
                        message=message,
                        line=i,
                        suggestion=suggestion
                    ))
        
        return issues
    
    def smell_detection(self, code: str) -> List[Issue]:
        """Detect code smells"""
        issues = []
        lines = code.split('\n')
        
        for pattern, message, suggestion in self.CODE_SMELLS:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(Issue(
                        severity=Severity.MEDIUM,
                        category="CODE_SMELL",
                        message=message,
                        line=i,
                        suggestion=suggestion
                    ))
        
        return issues
    
    def check_best_practices(self, code: str) -> Tuple[List[str], List[str], int]:
        """
        Check for best practices.
        
        Returns:
            (present, missing, bonus_score)
        """
        present = []
        missing = []
        bonus = 0
        
        for pattern, name, points in self.GOOD_PRACTICES:
            if re.search(pattern, code, re.MULTILINE):
                present.append(name)
                bonus += points
            else:
                missing.append(name)
        
        return present, missing, bonus
    
    def runtime_test(self, code: str) -> Dict[str, Any]:
        """
        Execute code in isolated sandbox with timeout.
        
        Returns execution result and any runtime errors.
        """
        result = {
            "executed": False,
            "output": "",
            "error": None,
            "execution_time": 0,
            "memory_estimate": "N/A"
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            # Wrap code to prevent hanging
            wrapped_code = f'''
import sys
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Execution timed out")

# Set timeout on Unix systems
if hasattr(signal, 'SIGALRM'):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm({self.timeout})

try:
{self._indent_code(code, 4)}
except Exception as e:
    print(f"RUNTIME_ERROR: {{type(e).__name__}}: {{e}}", file=sys.stderr)
finally:
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)
'''
            f.write(wrapped_code)
            temp_path = f.name
        
        try:
            start = time.time()
            
            # Run in subprocess with timeout
            proc = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout + 1,
                cwd=tempfile.gettempdir()
            )
            
            result["execution_time"] = round(time.time() - start, 3)
            result["executed"] = True
            result["output"] = proc.stdout[:2000] if proc.stdout else ""
            
            if proc.returncode != 0 or proc.stderr:
                stderr = proc.stderr[:1000] if proc.stderr else ""
                if "RUNTIME_ERROR:" in stderr:
                    result["error"] = stderr.split("RUNTIME_ERROR:")[-1].strip()
                elif stderr:
                    result["error"] = stderr
                    
        except subprocess.TimeoutExpired:
            result["error"] = "Execution timed out (possible infinite loop)"
        except Exception as e:
            result["error"] = f"Sandbox error: {str(e)}"
        finally:
            # Cleanup
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return result
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block"""
        indent = ' ' * spaces
        return '\n'.join(indent + line for line in code.split('\n'))
    
    def calculate_score(
        self,
        syntax_ok: bool,
        security_issues: List[Issue],
        smell_issues: List[Issue],
        bonus: int,
        runtime_ok: bool
    ) -> int:
        """Calculate final QA score (0-100)"""
        score = 100
        
        # Syntax is critical
        if not syntax_ok:
            score -= 60
        
        # Security issues
        for issue in security_issues:
            if issue.severity == Severity.CRITICAL:
                score -= 25
            elif issue.severity == Severity.HIGH:
                score -= 15
        
        # Code smells
        score -= len(smell_issues) * 3
        
        # Runtime failure
        if not runtime_ok:
            score -= 15
        
        # Bonus for good practices (cap at 20)
        score += min(bonus, 20)
        
        return max(0, min(100, score))
    
    def full_validation(self, code: str, run_tests: bool = True) -> Dict[str, Any]:
        """
        Complete code validation.
        
        Args:
            code: Python code to validate
            run_tests: Whether to run sandbox tests
            
        Returns:
            Comprehensive QA report
        """
        self.issues = []
        
        report = {
            "valid": True,
            "score": 100,
            "syntax": {"ok": True, "message": "", "line": None},
            "security": [],
            "smells": [],
            "best_practices": {"present": [], "missing": []},
            "ast_metrics": {},
            "runtime": {},
            "issues": [],
            "verdict": "PENDING",
            "grade": "A"
        }
        
        # 1. Syntax Check (Critical)
        syntax_ok, syntax_msg, syntax_line = self.validate_syntax(code)
        report["syntax"] = {
            "ok": syntax_ok,
            "message": syntax_msg,
            "line": syntax_line
        }
        
        if not syntax_ok:
            report["valid"] = False
            report["issues"].append(f"[CRITICAL] Syntax: {syntax_msg}")
            self.issues.append(Issue(Severity.CRITICAL, "SYNTAX", syntax_msg, syntax_line))
        
        # 2. AST Analysis
        if syntax_ok:
            report["ast_metrics"] = self.analyze_ast(code)
        
        # 3. Security Scan (High Priority)
        security_issues = self.security_scan(code)
        report["security"] = [
            {"severity": i.severity.value, "message": i.message, "line": i.line, "fix": i.suggestion}
            for i in security_issues
        ]
        for issue in security_issues:
            report["issues"].append(f"[{issue.severity.value}] Security: {issue.message} (line {issue.line})")
        self.issues.extend(security_issues)
        
        # 4. Code Smell Detection
        smell_issues = self.smell_detection(code)
        report["smells"] = [
            {"message": i.message, "line": i.line, "fix": i.suggestion}
            for i in smell_issues
        ]
        for issue in smell_issues:
            report["issues"].append(f"[MEDIUM] Smell: {issue.message} (line {issue.line})")
        self.issues.extend(smell_issues)
        
        # 5. Best Practices
        present, missing, bonus = self.check_best_practices(code)
        report["best_practices"] = {"present": present, "missing": missing, "bonus": bonus}
        
        # 6. Runtime Test (if enabled and syntax OK)
        runtime_ok = True
        if run_tests and syntax_ok:
            report["runtime"] = self.runtime_test(code)
            runtime_ok = report["runtime"]["executed"] and not report["runtime"].get("error")
            if not runtime_ok and report["runtime"].get("error"):
                report["issues"].append(f"[HIGH] Runtime: {report['runtime']['error']}")
        
        # 7. Calculate Score
        report["score"] = self.calculate_score(
            syntax_ok, security_issues, smell_issues, bonus, runtime_ok
        )
        
        # 8. Determine Verdict & Grade
        if report["score"] >= 90 and not security_issues:
            report["verdict"] = "APPROVED"
            report["grade"] = "A"
        elif report["score"] >= 80 and len([i for i in security_issues if i.severity == Severity.CRITICAL]) == 0:
            report["verdict"] = "APPROVED"
            report["grade"] = "B"
        elif report["score"] >= 70:
            report["verdict"] = "APPROVED_WITH_WARNINGS"
            report["grade"] = "C"
        elif report["score"] >= 50:
            report["verdict"] = "NEEDS_REVISION"
            report["grade"] = "D"
        else:
            report["verdict"] = "REJECTED"
            report["grade"] = "F"
            report["valid"] = False
        
        return report
    
    def format_report(self, report: Dict) -> str:
        """Format report for human reading"""
        lines = [
            "",
            "=" * 60,
            "          QA VALIDATION REPORT - NEXUS 10",
            "=" * 60,
            "",
            f"  SCORE:   {report['score']}/100",
            f"  GRADE:   {report['grade']}",
            f"  VERDICT: {report['verdict']}",
            "",
            "-" * 60,
            "  SYNTAX",
            "-" * 60,
            f"  {'[OK]' if report['syntax']['ok'] else '[FAIL]'} {report['syntax']['message']}",
            ""
        ]
        
        if report["security"]:
            lines.extend([
                "-" * 60,
                "  SECURITY ISSUES",
                "-" * 60
            ])
            for s in report["security"]:
                lines.append(f"  [{s['severity']}] Line {s['line']}: {s['message']}")
                lines.append(f"           Fix: {s['fix']}")
            lines.append("")
        
        if report["smells"]:
            lines.extend([
                "-" * 60,
                "  CODE SMELLS",
                "-" * 60
            ])
            for s in report["smells"][:5]:  # Limit to 5
                lines.append(f"  [!] Line {s['line']}: {s['message']}")
            lines.append("")
        
        lines.extend([
            "-" * 60,
            "  BEST PRACTICES",
            "-" * 60
        ])
        for p in report["best_practices"]["present"]:
            lines.append(f"  [+] {p}")
        for m in report["best_practices"]["missing"][:5]:
            lines.append(f"  [-] Missing: {m}")
        lines.append("")
        
        if report.get("runtime") and report["runtime"].get("executed"):
            lines.extend([
                "-" * 60,
                "  RUNTIME TEST",
                "-" * 60,
                f"  Executed: {'Yes' if report['runtime']['executed'] else 'No'}",
                f"  Time: {report['runtime']['execution_time']}s"
            ])
            if report["runtime"].get("error"):
                lines.append(f"  Error: {report['runtime']['error']}")
            lines.append("")
        
        if report.get("ast_metrics") and not report["ast_metrics"].get("error"):
            m = report["ast_metrics"]
            lines.extend([
                "-" * 60,
                "  CODE METRICS",
                "-" * 60,
                f"  Functions: {len(m.get('functions', []))}",
                f"  Classes: {len(m.get('classes', []))}",
                f"  Cyclomatic Complexity: {m.get('complexity', 0)}",
                f"  Max Nesting: {m.get('nested_depth', 0)}",
                ""
            ])
        
        lines.extend([
            "=" * 60,
            f"  FINAL: {report['verdict']} (Grade {report['grade']})",
            "=" * 60,
            ""
        ])
        
        return "\n".join(lines)
    
    def get_fix_suggestions(self, report: Dict) -> List[str]:
        """Get actionable fix suggestions"""
        suggestions = []
        
        for sec in report.get("security", []):
            suggestions.append(f"Security Fix: {sec['fix']}")
        
        for smell in report.get("smells", [])[:3]:
            suggestions.append(f"Code Improvement: {smell['fix']}")
        
        for missing in report["best_practices"]["missing"][:3]:
            suggestions.append(f"Add: {missing}")
        
        return suggestions


# =============================================================================
# QUICK HELPERS
# =============================================================================

def validate_code(code: str, run_tests: bool = False) -> Dict:
    """Quick validation function"""
    validator = QAValidator()
    return validator.full_validation(code, run_tests=run_tests)


def get_qa_score(code: str) -> int:
    """Get just the score"""
    report = validate_code(code, run_tests=False)
    return report["score"]


def is_code_approved(code: str) -> bool:
    """Check if code passes QA"""
    report = validate_code(code)
    return report["verdict"] in ["APPROVED", "APPROVED_WITH_WARNINGS"]


def quick_check(code: str) -> Tuple[bool, int, str]:
    """Quick check returning (is_valid, score, verdict)"""
    report = validate_code(code, run_tests=False)
    return report["valid"], report["score"], report["verdict"]


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("    QA VALIDATOR v3.0 - Testing")
    print("=" * 60)
    
    # Test with sample code
    test_code = '''# -*- coding: utf-8 -*-
"""
Bitcoin Price Monitor
Author: NEXUS 10 AI Agency
"""
import requests
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_btc_price() -> Optional[float]:
    """
    Get current BTC price from CoinGecko.
    
    Returns:
        float: Current price in USD, or None on error
    """
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "usd"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()["bitcoin"]["usd"]
    except requests.RequestException as e:
        logger.error(f"API error: {e}")
        return None

def main():
    """Main function"""
    price = get_btc_price()
    if price:
        logger.info(f"BTC Price: ${price:,.2f}")
    else:
        logger.warning("Could not fetch price")

if __name__ == "__main__":
    main()
'''
    
    validator = QAValidator()
    report = validator.full_validation(test_code, run_tests=True)
    print(validator.format_report(report))
    
    print("\nSuggestions:")
    for sug in validator.get_fix_suggestions(report):
        print(f"  - {sug}")
