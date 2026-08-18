import asyncio
import json
import logging
import os
import time

try:
    import websockets  # type: ignore
except ImportError:
    websockets = None

from .bot import CodeAssistantBot
from .renderer import VisualizadorPygame
from .rules import GameRules


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeChallengeWS")


class CodeChallengeWSClient:
    def __init__(
        self,
        token: str = "",
        bot=None,
        auth_token: str | None = None,
        rules: GameRules | None = None,
    ):
        final_token = auth_token or os.getenv("AUTH_TOKEN", token)

        self.url = (
            "wss://server.codechallenge.net.ar/ws"
            f"?token={final_token}"
        )

        self.bot = bot or CodeAssistantBot
        self.rules = rules

        self.history = {}
        self.visualizador = None
        self.target_game_id = None

    def _log_event(
        self,
        game_id: str,
        message: dict,
        direction: str = "<",
    ):
        self.history.setdefault(game_id, []).append(
            f"{direction} {json.dumps(message)}"
        )

    def _write_game_log(self, game_id: str):
        try:
            with open(f"game_{game_id}.log", "w") as f:
                f.write(
                    "\n".join(
                        self.history.get(game_id, [])
                    )
                    + "\n"
                )

            logger.info(
                "💾 Log guardado: game_%s.log",
                game_id,
            )

        except OSError as e:
            logger.error(
                "Error escribiendo log: %s",
                e,
            )

    async def send_action(
        self,
        ws,
        action: str,
        data: dict,
    ):
        payload = {
            "action": action,
            "data": data,
        }

        logger.info(
            "> %s",
            json.dumps(payload),
        )

        await ws.send(
            json.dumps(payload)
        )

    async def join_game(
        self,
        ws,
        game_id: str,
    ):
        """Envía la orden para unirse a una partida existente."""
        payload = {
            "action": "join_game",
            "data": {
                "game_id": game_id,
            },
        }

        logger.info(
            "Uniéndose a la partida %s...",
            game_id,
        )

        await self.send_action(
            ws,
            payload["action"],
            payload["data"],
        )

    async def start(self):
        if websockets is None:
            logger.error(
                "Instalá websockets antes de ejecutar el cliente."
            )
            return

        while True:
            try:
                logger.info(
                    "Conectando a %s...",
                    self.url,
                )

                async with websockets.connect(self.url) as ws:
                    logger.info(
                        "¡Conexión READY!"
                    )

                    if self.target_game_id:
                        await self.send_action(
                            ws,
                            "join_game",
                            {
                                "game_id": self.target_game_id,
                            },
                        )

                    await self._listen_loop(ws)

            except KeyboardInterrupt:
                logger.info(
                    "Cliente detenido."
                )
                break

            except Exception as e:
                logger.error(
                    "Connection error: %s",
                    e,
                )

                await asyncio.sleep(3)

    async def _listen_loop(self, ws):
        async for raw_message in ws:
            try:
                logger.info(
                    "< %s",
                    raw_message,
                )

                request_data = json.loads(
                    raw_message
                )

                event = request_data.get(
                    "event"
                )

                if event == "challenge":
                    await self._handle_challenge(
                        ws,
                        request_data,
                    )

                elif event == "your_turn":
                    await self._handle_turn(
                        ws,
                        request_data,
                    )

                elif event == "game_over":
                    self._handle_game_over(
                        request_data
                    )

            except json.JSONDecodeError:
                logger.warning(
                    "Mensaje no formateado en JSON."
                )

            except Exception as e:
                logger.error(
                    "Error procesando evento: %s",
                    e,
                )

    async def _handle_challenge(
        self,
        ws,
        request_data: dict,
    ):
        data = request_data.get(
            "data",
            {},
        )

        await self.send_action(
            ws,
            "accept_challenge",
            {
                "challenge_id": data.get(
                    "challenge_id"
                )
            },
        )

    async def _handle_turn(
        self,
        ws,
        request_data: dict,
    ):
        t_start = time.perf_counter()

        data = request_data.get(
            "data",
            {},
        )

        game_id = (
            request_data.get("game_id")
            or data.get("game_id")
        )

        turn_token = (
            request_data.get("turn_token")
            or data.get("turn_token")
        )

        board = data.get(
            "board"
        ) or {}

        side = data.get(
            "side"
        )

        rows = data.get(
            "rows",
            20,
        )

        cols = data.get(
            "cols",
            20,
        )

        remaining_moves = data.get(
            "remaining_moves"
        )

        self._log_event(
            game_id,
            request_data,
            "<",
        )

        self._render_board(
            board,
            side,
            rows,
            cols,
        )

        payload_for_bot = {
            "board": board,
            "rows": rows,
            "cols": cols,
            "side": side,
            "remaining_moves": remaining_moves,
            "turn_token": turn_token,
            "game_id": game_id,
            "rules": self.rules,
        }

        result = self.bot.process_request(  # type: ignore
            "calculate_move",
            payload_for_bot,
        )

        if not result.success:
            logger.warning(
                "Bot falló en calculate_move: %s",
                result.output,
            )

        direction = self._get_valid_direction(
            result.output
        )

        move_payload = {
            "game_id": game_id,
            "turn_token": turn_token,
            "direction": direction,
        }

        self._log_event(
            game_id,
            {
                "action": "move",
                "data": move_payload,
            },
            ">",
        )

        await self.send_action(
            ws,
            "move",
            move_payload,
        )

        t_end = time.perf_counter()

        total_e2e_ms = (
            t_end - t_start
        ) * 1000

        logger.info(
            "⏱️ Tiempo Total WSS "
            "(Pygame + Bot + WS Send): %.2f ms",
            total_e2e_ms,
        )

    def _render_board(
        self,
        board: dict,
        side: str,
        rows: int,
        cols: int,
    ):
        if self.visualizador is None:
            self.visualizador = VisualizadorPygame(
                ancho_grid=cols,
                alto_grid=rows,
            )

        mi_cuerpo = (
            board.get("my_snake")
            or board.get(side)
            or []
        )

        rival_side = (
            "P2"
            if side == "P1"
            else "P1"
        )

        cuerpo_rival = (
            board.get("enemy_snake")
            or board.get(rival_side)
            or []
        )

        manzana = (
            board.get("apple")
            or board.get("food")
        )

        self.visualizador.renderizar(
            {
                "apple": manzana,
                "dev_sentinel": mi_cuerpo,
                "rival_bot": cuerpo_rival,
            }
        )

    @staticmethod
    def _get_valid_direction(output):
        valid_directions = {
            "UP",
            "DOWN",
            "LEFT",
            "RIGHT",
            "up",
            "down",
            "left",
            "right",
        }

        direction = None

        if isinstance(output, dict):
            direction = output.get(
                "direction"
            )

        if direction not in valid_directions:
            logger.warning(
                "Dirección inválida del bot: %s. "
                "Usando 'right' por seguridad.",
                direction,
            )

            return "right"

        return direction.lower()

    def _handle_game_over(
        self,
        request_data: dict,
    ):
        game_id = request_data.get(
            "game_id"
        )

        if game_id:
            self._log_event(
                game_id,
                request_data,
                "<",
            )

            self._write_game_log(
                game_id
            )

        if self.visualizador is not None:
            self.visualizador.cerrar()
            self.visualizador = None