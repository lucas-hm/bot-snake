import subprocess
from interfaces import IBotCommand, CommandResult


class AutoFormatterTool(IBotCommand):
    @property
    def name(self) -> str:
        return "format"

    def execute(self, code_snippet: str, **kwargs) -> CommandResult:
        try:
            process = subprocess.run(
                ["black", "-q", "-"],
                input=code_snippet,
                capture_output=True,
                text=True,
                check=True
            )
            return CommandResult(
                success=True,
                output=process.stdout,
                metadata={"engine": "black"}
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return CommandResult(
                success=True,
                output=code_snippet.strip() + "\n",
                metadata={"engine": "native_fallback"}
            )
