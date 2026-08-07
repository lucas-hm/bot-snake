import asyncio
from bot import CodeAssistantBot
from ws_client import CodeChallengeWSClient
from game_engine import GameMoveTool
from tools.ast_analyzer import ASTMetricsAnalyzer
from tools.security_tool import SecurityGuardTool

def build_bot() -> CodeAssistantBot:
    bot = CodeAssistantBot("DevSentinel")
    bot.register_command(ASTMetricsAnalyzer())
    bot.register_command(SecurityGuardTool())
    bot.register_command(GameMoveTool())
    return bot

if __name__ == "__main__":
    MY_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoibHVjYXNtb3JhbiJ9.v9EzLD_0HKOzcCJW_dTb1hdAoOdX4OnJcbFVeyH12a8"
    
    # 1. Pedir el ID de la partida por consola si es necesario
    target_game_id = input("Ingresá el ID de la partida (presioná Enter para modo automático/desafíos): ").strip()
    
    bot_instance = build_bot()
    ws_client = CodeChallengeWSClient(token=MY_TOKEN, bot=bot_instance)

    # Si ingresaste un game_id, se lo pasas al cliente para que se una al conectar
    if target_game_id:
        ws_client.target_game_id = target_game_id # type: ignore

    asyncio.run(ws_client.start())