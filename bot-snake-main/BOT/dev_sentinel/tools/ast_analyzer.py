import ast
from ..interfaces import IBotCommand, CommandResult

class ASTMetricsAnalyzer(IBotCommand):
    @property
    def name(self) -> str:
        return "analyze"

    def execute(self, code_snippet: str, **kwargs) -> CommandResult:
        try:
            tree = ast.parse(code_snippet)
            functions = [node.name for node in ast.walk(
                tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(
                tree) if isinstance(node, ast.ClassDef)]

            metrics = {
                "total_functions": len(functions),
                "total_classes": len(classes),
                "functions_list": functions,
                "classes_list": classes
            }

            out_msg = f"Análisis AST exitoso. Clases: {', '.join(classes) if classes else 'Ninguna'}, Funciones: {', '.join(functions) if functions else 'Ninguna'}."
            return CommandResult(success=True, output=out_msg, metadata=metrics)

        except SyntaxError as e:
            return CommandResult(
                success=False,
                output=f"Error de sintaxis en el código: {e.msg} (Línea {e.lineno})"
            )