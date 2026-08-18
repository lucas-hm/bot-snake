import sys

import pygame  # type: ignore


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
        """Renderiza el estado actual de la partida."""
        for event in pygame.event.get():  # type: ignore
            if event.type == pygame.QUIT:  # type: ignore
                pygame.quit()  # type: ignore
                sys.exit()

        self.screen.fill(self.COLOR_FONDO)

        self._dibujar_manzana(estado)

        cuerpo_dev = estado.get("dev_sentinel", [])
        cuerpo_rival = estado.get("rival_bot", [])

        serpiente_pequena = self._obtener_serpiente_pequena(
            cuerpo_dev,
            cuerpo_rival,
        )

        self._dibujar_serpiente(
            cuerpo_dev,
            "dev_sentinel",
            serpiente_pequena,
            self.COLOR_DEV,
        )

        self._dibujar_serpiente(
            cuerpo_rival,
            "rival_bot",
            serpiente_pequena,
            self.COLOR_RIVAL,
        )

        pygame.display.flip()  # type: ignore

    def _dibujar_manzana(self, estado):
        apple = estado.get("apple")

        if not apple:
            return

        ax, ay = apple

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

    def _obtener_serpiente_pequena(
        self,
        cuerpo_dev,
        cuerpo_rival,
    ):
        len_dev = len(cuerpo_dev)
        len_rival = len(cuerpo_rival)

        if len_dev == 0 or len_rival == 0:
            return None

        if len_dev < len_rival:
            return "dev_sentinel"

        if len_rival < len_dev:
            return "rival_bot"

        return None

    def _dibujar_serpiente(
        self,
        cuerpo,
        nombre,
        serpiente_pequena,
        color_base,
    ):
        longitud = len(cuerpo)

        for i, segment in enumerate(cuerpo):
            color = color_base

            if (
                serpiente_pequena == nombre
                and i == longitud - 1
                and longitud > 1
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

    def cerrar(self):
        """Cierra correctamente Pygame."""
        pygame.quit()  # type: ignore