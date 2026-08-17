import asyncio
from .bot import CodeAssistantBot
from .ws_client import CodeChallengeWSClient
from .game_engine import GameMoveTool
from .rules import GameRules
from tools.ast_analyzer import ASTMetricsAnalyzer
from tools.security_tool import SecurityGuardTool

def build_bot() -> CodeAssistantBot:
    bot = CodeAssistantBot("DevSentinel")
    bot.register_command(ASTMetricsAnalyzer())
    bot.register_command(SecurityGuardTool())
    bot.register_command(GameMoveTool())
    return bot

def build_rules() -> GameRules:
    """Create the rules used by the current game."""
    return GameRules(max_moves=100)

if __name__ == "__main__":
    MY_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZGV2c2VudGluZWwifQ.Mg8HNaGaAaQql0zsbq9a0r8IZTCAeVYNKh3cmGgGBk8"

    # Rules used by the current game.
    rules = build_rules()

    # Ask for the game ID if necessary.
    target_game_id = input(
        "Ingresá el ID de la partida "
        "(presioná Enter para modo automático/desafíos): "
    ).strip()

    bot_instance = build_bot()

    ws_client = CodeChallengeWSClient(
        token=MY_TOKEN,
        bot=bot_instance, # type: ignore
        rules=rules # type: ignore
    )  # type: ignore

    if target_game_id:
        ws_client.target_game_id = target_game_id  # type: ignore

    asyncio.run(ws_client.start())