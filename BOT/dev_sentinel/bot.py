from interfaces import IBotCommand, CommandResult

class CodeAssistantBot:
    def __init__(self, bot_name: str = "DevSentinel"):
        self.bot_name = bot_name
        self._registry: dict[str, IBotCommand] = {}

    def register_command(self, command: IBotCommand) -> None:
        self._registry[command.name] = command

    def process_request(self, command_name: str, payload: any, **kwargs) -> CommandResult: # type: ignore
        if command_name not in self._registry:
            return CommandResult(
                success=False, 
                output=f"Comando '{command_name}' no registrado."
            )
        return self._registry[command_name].execute(payload, **kwargs)
