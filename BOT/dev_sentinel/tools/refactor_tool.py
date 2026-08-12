import ast
from interfaces import IBotCommand, CommandResult


class RefactorTool(IBotCommand):
    @property
    def name(self) -> str:
        return "refactor"

    def execute(self, code_snippet: str, **kwargs) -> CommandResult:
        try:
            tree = ast.parse(code_snippet)

            class RefactorTransformer(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    self.generic_visit(node)
                    if not ast.get_docstring(node):
                        doc = ast.Expr(value=ast.Constant(
                            value="Docstring generado automáticamente."))
                        node.body.insert(0, doc)
                    return node

            transformed_tree = RefactorTransformer().visit(tree)
            ast.fix_missing_locations(transformed_tree)

            return CommandResult(
                success=True,
                output=ast.unparse(transformed_tree),
                metadata={"refactored_nodes": len(transformed_tree.body)}
            )
        except Exception as e:
            return CommandResult(success=False, output=f"Error en refactorización: {str(e)}")
