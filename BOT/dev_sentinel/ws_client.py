import asyncio
import json
import logging
import time

try:
    import websockets # type: ignore
except ImportError:
    websockets = None

from bot import CodeAssistantBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeChallengeWS")

class CodeChallengeWSClient:
    def __init__(self, token: str, bot: CodeAssistantBot, base_url: str = "wss://codechallenge-server.up.railway.app/ws"):
        self.url = f"{base_url}?token={token}"
        self.bot = bot
        self.history = {}

    def _log_event(self, game_id: str, message: dict, direction: str = "<"):
        self.history.setdefault(game_id, []).append(f"{direction} {json.dumps(message)}")

    def _write_game_log(self, game_id: str):
        try:
            with open(f"game_{game_id}.log", "w") as f:
                f.write("\n".join(self.history.get(game_id, [])) + "\n")
            logger.info(f"💾 Log guardado: game_{game_id}.log")
        except OSError as e:
            logger.error(f"Error escribiendo log: {e}")

    async def send_action(self, ws, action: str, data: dict):
        payload = {"action": action, "data": data}
        logger.info(f"> {json.dumps(payload)}")
        await ws.send(json.dumps(payload))

    async def start(self):
        if websockets is None:
            logger.error("Instalá websockets con pip install websockets o vía nix-shell")
            return

        while True:
            try:
                logger.info(f"Conectando a {self.url}...")
                async with websockets.connect(self.url) as ws:
                    logger.info("¡Conexión READY!")
                    await self._listen_loop(ws)
            except KeyboardInterrupt:
                logger.info("Exiting...")
                break
            except Exception as e:
                logger.error(f"Connection error: {e}")
                time.sleep(3)

    async def _listen_loop(self, ws):
        async for raw_message in ws:
            try:
                logger.info(f"< {raw_message}")
                request_data = json.loads(raw_message)
                event = request_data.get("event")
                data = request_data.get("data", {})

                # Evento: Desafío entrante
                if event == "challenge":
                    await self.send_action(
                        ws, 
                        "accept_challenge", 
                        {"challenge_id": data.get("challenge_id")}
                    )

                # Evento: Tu turno
                elif event == "your_turn":
                    game_id = data.get("game_id")
                    self._log_event(game_id, request_data, "<")
                    
                    # Llamamos al bot para calcular jugada
                    result = self.bot.process_request("calculate_move", data)
                    if result.success:
                        self._log_event(game_id, {"action": "move", "data": result.output}, ">")
                        await self.send_action(ws, "move", result.output)

                # Evento: Fin de partida
                elif event == "game_over":
                    game_id = data.get("game_id")
                    if game_id:
                        self._log_event(game_id, request_data, "<")
                        self._write_game_log(game_id)

            except json.JSONDecodeError:
                logger.warning("Mensaje no formateado en JSON.")
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")