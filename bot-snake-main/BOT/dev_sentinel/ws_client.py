import asyncio
import json
import logging
import sys
import time
import os

try:
    import websockets  # type: ignore
except ImportError:
    websockets = None

from bot import CodeAssistantBot
# Importamos Pygame para el renderer de interfaz gráfica
import pygame # type: ignore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CodeChallengeWS")


class VisualizadorPygame:

    def __init__(self, ancho_grid=20, alto_grid=20):
        pygame.init()  # type: ignore
        self.COLOR_FONDO = (20, 20, 20)
        self.COLOR_MANZANA = (255, 50, 50)  # Rojo
        self.COLOR_DEV = (0, 230, 0)  # Verde
        self.COLOR_RIVAL = (50, 150, 255)  # Azul
        self.COLOR_COLA_PEQUENA = (255, 0, 0)  # Rojo cola

        self.ancho_pantalla = 1920
        self.alto_pantalla = 1080

        self.tam_celda = min(
            self.ancho_pantalla // ancho_grid, self.alto_pantalla // alto_grid
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
        pygame.display.set_caption("Partida Bot Snake - dev_sentinel")  # type: ignore

    def renderizar(self, estado):
        for event in pygame.event.get():  # type: ignore
            if event.type == pygame.QUIT:  # type: ignore
                pygame.quit()  # type: ignore
                sys.exit()

        self.screen.fill(self.COLOR_FONDO)

        # Dibujar Manzana
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

        # Dibujar dev_sentinel (Verde)
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

        # Dibujar Bot Rival (Azul)
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
        token: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiZGV2c2VudGluZWwifQ.Mg8HNaGaAaQql0zsbq9a0r8IZTCAeVYNKh3cmGgGBk8",
        bot = CodeAssistantBot,
        auth_token: str | None = None,
    ):
        final_token = auth_token or os.getenv("AUTH_TOKEN", token)
        self.url = f"wss://server.codechallenge.net.ar/ws?token={final_token}"
        self.bot = bot
        self.history = {}
        self.visualizador = None  # Instancia dinámica del render de Pygame

    def _log_event(self, game_id: str, message: dict, direction: str = "<"):
        self.history.setdefault(game_id, []).append(
            f"{direction} {json.dumps(message)}"
        )

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
        payload = {"action": "join_game", "data": {"game_id": game_id}}
        logger.info(f"Uniéndose a la partida {game_id}...")
        await self.send_action(ws, payload["action"], payload["data"])

    async def start(self):
        if websockets is None:
            logger.error("Instalá websockets...")
            return

        while True:
            try:
                logger.info(f"Conectando a {self.url}...")
                async with websockets.connect(self.url) as ws:
                    logger.info("¡Conexión READY!")

                    if (
                        hasattr(self, "target_game_id") and self.target_game_id  # type: ignore
                    ):  # type: ignore
                        await self.send_action(ws, "join_game", {"game_id": self.target_game_id})  # type: ignore

                    await self._listen_loop(ws)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(3)

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
                        {"challenge_id": data.get("challenge_id")},
                    )

                # Evento: Tu turno
                elif event == "your_turn":
                    # ⏱️ 1. Iniciar reloj al recibir el mensaje de la red
                    t_start = time.perf_counter()

                    data = request_data.get("data", {})
                    game_id = request_data.get("game_id") or data.get("game_id")
                    turn_token = request_data.get("turn_token") or data.get(
                        "turn_token"
                    )
                    board = data.get("board") or {}
                    side = data.get("side")
                    rows = data.get("rows", 20)
                    cols = data.get("cols", 20)
                    remaining_moves = data.get("remaining_moves")

                    self._log_event(game_id, request_data, "<")

                    # 1. Crear ventana gráfica de Pygame si aún no existe
                    if self.visualizador is None:
                        self.visualizador = VisualizadorPygame(
                            ancho_grid=cols, alto_grid=rows
                        )

                    # 2. Extraer posiciones del 'board' para renderizar
                    mi_cuerpo = board.get("my_snake") or board.get(side) or []
                    rival_side = "P2" if side == "P1" else "P1"
                    cuerpo_rival = board.get("enemy_snake") or board.get(rival_side) or []
                    manzana = board.get("apple") or board.get("food")

                    # 3. Renderizar tablero en pantalla
                    self.visualizador.renderizar(
                        {
                            "apple": manzana,
                            "dev_sentinel": mi_cuerpo,
                            "rival_bot": cuerpo_rival,
                        }
                    )

                    # 4. Cálculo y respuesta del movimiento
                    payload_for_bot = {
                        "board": board,
                        "rows": rows,
                        "cols": cols,
                        "side": side,
                        "remaining_moves": remaining_moves,
                        "turn_token": turn_token,
                        "game_id": game_id,
                    }

                    result = self.bot.process_request( # type: ignore
                        "calculate_move", payload_for_bot
                    )

                    if not result.success:
                        logger.warning(
                            "Bot falló en calculate_move: %s",
                            result.output,
                        )

                    direction = None
                    if isinstance(result.output, dict):
                        direction = result.output.get("direction")

                    valid_directions = {"UP", "DOWN", "LEFT", "RIGHT", "up", "down", "left", "right"}
                    if direction not in valid_directions:
                        logger.warning(
                            "Dirección inválida del bot: %s. Usando 'right' por seguridad.",
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
                        {"action": "move", "data": move_payload},
                        ">",
                    )

                    # 🚀 Enviar respuesta por WebSocket
                    await self.send_action(ws, "move", move_payload)

                    # ⏱️ 2. Detener reloj tras enviar el paquete por la red
                    t_end = time.perf_counter()
                    total_e2e_ms = (t_end - t_start) * 1000
                    logger.info(f"⏱️ Tiempo Total WSS (Pygame + Bot + WS Send): {total_e2e_ms:.2f} ms")

                # Evento: Fin de partida
                elif event == "game_over":
                    game_id = request_data.get("game_id")
                    if game_id:
                        self._log_event(game_id, request_data, "<")
                        self._write_game_log(game_id)
                    # Reiniciamos el visualizador para la próxima partida
                    self.visualizador = None

            except json.JSONDecodeError:
                logger.warning("Mensaje no formateado en JSON.")
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")