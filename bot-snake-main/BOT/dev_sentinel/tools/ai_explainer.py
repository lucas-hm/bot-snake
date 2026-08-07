import ast
from interfaces import IBotCommand, CommandResult


class AIExplainerTool(IBotCommand):
    @property
    def name(self) -> str:
        return "explain"

    def execute(self, code_snippet: str, **kwargs) -> CommandResult:
        try:
            tree = ast.parse(code_snippet)
            funcs = [n.name for n in ast.walk(
                tree) if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in ast.walk(
                tree) if isinstance(n, ast.ClassDef)]

            explanation = (
                "🤖 **Resumen del Asistente IA**\n"
                f"• **Clases detectadas:** {
                    ', '.join(classes) if classes else 'Ninguna'}\n"
                f"• **Funciones principales:** {
                    ', '.join(funcs) if funcs else 'Ninguna'}\n"
                "• **Diagnóstico:** El código presenta una estructura coherente de Python."
            )
            return CommandResult(success=True, output=explanation, metadata={"type": "ai_response"})
        except Exception as e:
            return CommandResult(
                success=False,
                output=f"🤖 **Asistente IA:** Error sintáctico: {e}"
            )
