import asyncio
import json
import logging
import os
import sys
import time

try:
    import websockets  # type: ignore
except ImportError:
    websockets = None

import pygame  # type: ignore
from .bot import CodeAssistantBot
from .rules import GameRules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeChallengeWS")


class VisualizadorPygame:
    def __init__(self, ancho_grid=20, alto_grid=20):
        pygame.init()  # type: ignore

        self.COLOR_FONDO = (20, 20, 20)
        self.COLOR_MANZANA = (255, 50, 50)
        self.COLOR_DEV = (0, 230, 0)
        self.COLOR_RIVAL = (50, 150, 255)
        self.COLOR_COLA_PEQUENA = (255, 0, 0)

        self.ancho_pantalla = 1920
        self.alto_pantalla = 1080

        self.tam_celda = min(
            self.ancho_pantalla // ancho_grid,
            self.alto_pantalla // alto_grid,
        )

        self.margen_x = (
            self.ancho_pantalla - (ancho_grid * self.tam_celda)
        ) // 2

        self.margen_y = (
            self.alto_pantalla - (alto_grid * self.tam_celda)
        ) // 2

        self.screen = pygame.display.set_mode(  # type: ignore
            (self.ancho_pantalla, self.alto_pantalla)
        )

        pygame.display.set_caption(  # type: ignore
            "Partida Bot Snake - dev_sentinel"
        )

    def renderizar(self, estado):
        for event in pygame.event.get():  # type: ignore
            if event.type == pygame.QUIT:  # type: ignore
                pygame.quit()  # type: ignore
                sys.exit()

        self.screen.fill(self.COLOR_FONDO)

        # Dibujar manzana.
        if "apple" in estado and estado["apple"]:
            ax, ay = estado["apple"]

            pygame.draw.rect(  # type: ignore
                self.screen,
                self.COLOR_MANZANA,
                (
                    self.margen_x + ax * self.tam_celda,
                    self.margen_y + ay * self.tam_celda,
                    self.tam_celda,
                    self.tam_celda,
                ),
            )

        cuerpo_dev = estado.get("dev_sentinel", [])
        cuerpo_rival = estado.get("rival_bot", [])

        len_dev = len(cuerpo_dev)
        len_rival = len(cuerpo_rival)

        serpiente_pequena = None

        if len_dev > 0 and len_rival > 0:
            if len_dev < len_rival:
                serpiente_pequena = "dev_sentinel"
            elif len_rival < len_dev:
                serpiente_pequena = "rival_bot"

        # Dibujar dev_sentinel.
        for i, segment in enumerate(cuerpo_dev):
            color = self.COLOR_DEV

            if (
                serpiente_pequena == "dev_sentinel"
                and i == len_dev - 1
                and len_dev > 1
            ):
                color = self.COLOR_COLA_PEQUENA

            pygame.draw.rect(  # type: ignore
                self.screen,
                color,
                (
                    self.margen_x + segment[0] * self.tam_celda,
                    self.margen_y + segment[1] * self.tam_celda,
                    self.tam_celda,
                    self.tam_celda,
                ),
            )

        # Dibujar bot rival.
        for i, segment in enumerate(cuerpo_rival):
            color = self.COLOR_RIVAL

            if (
                serpiente_pequena == "rival_bot"
                and i == len_rival - 1
                and len_rival > 1
            ):
                color = self.COLOR_COLA_PEQUENA

            pygame.draw.rect(  # type: ignore
                self.screen,
                color,
                (
                    self.margen_x + segment[0] * self.tam_celda,
                    self.margen_y + segment[1] * self.tam_celda,
                    self.tam_celda,
                    self.tam_celda,
                ),
            )

        pygame.display.flip()  # type: ignore


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

                # Evento: desafío entrante.
                if event == "challenge":
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

                # Evento: turno del bot.
                elif event == "your_turn":
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

                    # Crear ventana gráfica si todavía no existe.
                    if self.visualizador is None:
                        self.visualizador = VisualizadorPygame(
                            ancho_grid=cols,
                            alto_grid=rows,
                        )

                    # Extraer posiciones del tablero.
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

                    # Renderizar tablero.
                    self.visualizador.renderizar(
                        {
                            "apple": manzana,
                            "dev_sentinel": mi_cuerpo,
                            "rival_bot": cuerpo_rival,
                        }
                    )

                    # Información enviada al bot.
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

                    direction = None

                    if isinstance(
                        result.output,
                        dict,
                    ):
                        direction = result.output.get(
                            "direction"
                        )

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

                    if direction not in valid_directions:
                        logger.warning(
                            "Dirección inválida del bot: %s. "
                            "Usando 'right' por seguridad.",
                            direction,
                        )

                        direction = "right"

                    else:
                        direction = direction.lower()

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

                    # Enviar movimiento.
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

                # Evento: fin de partida.
                elif event == "game_over":
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

                    # Preparar visualizador para otra partida.
                    self.visualizador = None

            except json.JSONDecodeError:
                logger.warning(
                    "Mensaje no formateado en JSON."
                )

            except Exception as e:
                logger.error(
                    "Error procesando evento: %s",
                    e,
                )