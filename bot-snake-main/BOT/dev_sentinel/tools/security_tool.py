import ast
import re
from interfaces import IBotCommand, CommandResult


class SecurityGuardTool(IBotCommand):
    @property
    def name(self) -> str:
        return "security_scan"

    def execute(self, code_snippet: str, **kwargs) -> CommandResult:
        issues = []
        try:
            tree = ast.parse(code_snippet)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ["eval", "exec", "input"]:
                        issues.append(f"Uso inseguro detectado: '{node.func.id}' en línea {node.lineno}")
        except SyntaxError:
            pass

        api_key_pattern = r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]"
        if re.search(api_key_pattern, code_snippet):
            issues.append(
                "ALERTA: Se detectó una API Key o Secret escrito directamente en código (Hardcoded).")

        is_safe = len(issues) == 0
        status_msg = "Código Seguro: Sin vulnerabilidades críticas." if is_safe else "\n".join(
            issues)

        return CommandResult(success=is_safe, output=status_msg, metadata={"issues_count": len(issues)})
