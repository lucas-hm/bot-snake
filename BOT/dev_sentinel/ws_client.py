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

    async def join_game(self, ws, game_id: str):
        """Envía la orden para unirse activamente a una partida existente."""
        payload = {
            "action": "join_game",
            "data": {"game_id": game_id}
        }
        logger.info(f"Uniéndose a la partida {game_id}...")
        await self.send_action(ws, payload["action"], payload["data"])
        
    # En ws_client.py
    async def start(self):
        if websockets is None:
            logger.error("Instalá websockets...")
            return

        while True:
            try:
                logger.info(f"Conectando a {self.url}...")
                async with websockets.connect(self.url) as ws:
                    logger.info("¡Conexión READY!")
                    
                    # Si especificaste una partida en main.py, entra automáticamente
                    if hasattr(self, 'target_game_id') and self.target_game_id: # type: ignore
                        await self.send_action(ws, "join_game", {"game_id": self.target_game_id}) # type: ignore

                    await self._listen_loop(ws)
            except KeyboardInterrupt:
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

                    # Evento: Desafío entrante
                    if event == "challenge":
                        data = request_data.get("data", {})
                        await self.send_action(
                            ws, 
                            "accept_challenge", 
                            {"challenge_id": data.get("challenge_id")}
                        )

                    # Evento: Tu turno
                    elif event == "your_turn":
                        data = request_data.get("data", {})
                        game_id = request_data.get("game_id") or data.get("game_id")
                        turn_token = request_data.get("turn_token") or data.get("turn_token")
                        board = data.get("board")
                        side = data.get("side")
                        rows = data.get("rows")
                        cols = data.get("cols")
                        remaining_moves = data.get("remaining_moves")

                        self._log_event(game_id, request_data, "<")

                        if board is None:
                            logger.warning(
                                "your_turn sin tablero válido. Datos recibidos: %s",
                                request_data,
                            )
                            board = {}

                        payload_for_bot = {
                            "board": board,
                            "rows": rows,
                            "cols": cols,
                            "side": side,
                            "remaining_moves": remaining_moves,
                            "turn_token": turn_token,
                            "game_id": game_id,
                        }

                        result = self.bot.process_request("calculate_move", payload_for_bot)

                        if not result.success:
                            logger.warning(
                                "Bot falló en calculate_move: %s",
                                result.output,
                            )

                        direction = None
                        if isinstance(result.output, dict):
                            direction = result.output.get("direction")

                        if direction not in {"UP", "DOWN", "LEFT", "RIGHT"}:
                            logger.warning(
                                "Dirección inválida del bot: %s. Usando RIGHT por seguridad.",
                                direction,
                            )
                            direction = "RIGHT"

                        move_payload = {
                            "game_id": game_id,
                            "turn_token": turn_token,
                            "direction": direction,
                        }

                        self._log_event(game_id, {"action": "move", "data": move_payload}, ">")
                        await self.send_action(ws, "move", move_payload)

                    # Evento: Fin de partida
                    elif event == "game_over":
                        game_id = request_data.get("game_id")
                        if game_id:
                            self._log_event(game_id, request_data, "<")
                            self._write_game_log(game_id)

                except json.JSONDecodeError:
                    logger.warning("Mensaje no formateado en JSON.")
                except Exception as e:
                    logger.error(f"Error procesando evento: {e}")