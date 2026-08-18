import unittest
from unittest.mock import MagicMock, patch

from BOT.dev_sentinel.renderer import VisualizadorPygame

class TestVisualizadorPygame(unittest.TestCase):

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_init_configura_pygame(self, mock_pygame):
        mock_pygame.display.set_mode.return_value = MagicMock()

        renderer = VisualizadorPygame(
            ancho_grid=20,
            alto_grid=20,
        )

        mock_pygame.init.assert_called_once()
        mock_pygame.display.set_mode.assert_called_once_with(
            (1920, 1080)
        )
        mock_pygame.display.set_caption.assert_called_once_with(
            "Partida Bot Snake - dev_sentinel"
        )

        self.assertEqual(renderer.ancho_pantalla, 1920)
        self.assertEqual(renderer.alto_pantalla, 1080)

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_init_calcula_tamano_de_celda_y_margenes(
        self,
        mock_pygame,
    ):
        mock_pygame.display.set_mode.return_value = MagicMock()

        renderer = VisualizadorPygame(
            ancho_grid=20,
            alto_grid=20,
        )

        self.assertEqual(renderer.tam_celda, 54)
        self.assertEqual(renderer.margen_x, 420)
        self.assertEqual(renderer.margen_y, 0)

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_renderizar_dibuja_manzana(
        self,
        mock_pygame,
    ):
        mock_screen = MagicMock()
        mock_pygame.display.set_mode.return_value = mock_screen
        mock_pygame.event.get.return_value = []

        renderer = VisualizadorPygame()

        estado = {
            "apple": (5, 10),
            "dev_sentinel": [],
            "rival_bot": [],
        }

        renderer.renderizar(estado)

        mock_screen.fill.assert_called_once_with(
            renderer.COLOR_FONDO
        )

        mock_pygame.draw.rect.assert_called_once()

        mock_pygame.display.flip.assert_called_once()

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_renderizar_no_dibuja_manzana_si_no_existe(
        self,
        mock_pygame,
    ):
        mock_screen = MagicMock()
        mock_pygame.display.set_mode.return_value = mock_screen
        mock_pygame.event.get.return_value = []

        renderer = VisualizadorPygame()

        renderer.renderizar({
            "dev_sentinel": [],
            "rival_bot": [],
        })

        mock_pygame.draw.rect.assert_not_called()
        mock_pygame.display.flip.assert_called_once()

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_renderizar_dibuja_dev_sentinel(
        self,
        mock_pygame,
    ):
        mock_screen = MagicMock()
        mock_pygame.display.set_mode.return_value = mock_screen
        mock_pygame.event.get.return_value = []

        renderer = VisualizadorPygame()

        estado = {
            "dev_sentinel": [
                (1, 1),
                (2, 1),
                (3, 1),
            ],
            "rival_bot": [],
        }

        renderer.renderizar(estado)

        self.assertEqual(
            mock_pygame.draw.rect.call_count,
            3,
        )

        mock_pygame.display.flip.assert_called_once()

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_renderizar_dibuja_rival(
        self,
        mock_pygame,
    ):
        mock_screen = MagicMock()
        mock_pygame.display.set_mode.return_value = mock_screen
        mock_pygame.event.get.return_value = []

        renderer = VisualizadorPygame()

        estado = {
            "dev_sentinel": [],
            "rival_bot": [
                (5, 5),
                (6, 5),
            ],
        }

        renderer.renderizar(estado)

        self.assertEqual(
            mock_pygame.draw.rect.call_count,
            2,
        )

        mock_pygame.display.flip.assert_called_once()

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_renderizar_dibuja_ambas_serpientes(
        self,
        mock_pygame,
    ):
        mock_screen = MagicMock()
        mock_pygame.display.set_mode.return_value = mock_screen
        mock_pygame.event.get.return_value = []

        renderer = VisualizadorPygame()

        estado = {
            "dev_sentinel": [
                (1, 1),
                (2, 1),
            ],
            "rival_bot": [
                (10, 10),
                (11, 10),
                (12, 10),
            ],
        }

        renderer.renderizar(estado)

        self.assertEqual(
            mock_pygame.draw.rect.call_count,
            5,
        )

    def test_serpiente_dev_es_mas_pequena(self):
        renderer = object.__new__(VisualizadorPygame)

        resultado = renderer._obtener_serpiente_pequena(
            [(1, 1)],
            [(5, 5), (6, 5)],
        )

        self.assertEqual(
            resultado,
            "dev_sentinel",
        )

    def test_serpiente_rival_es_mas_pequena(self):
        renderer = object.__new__(VisualizadorPygame)

        resultado = renderer._obtener_serpiente_pequena(
            [(1, 1), (2, 1), (3, 1)],
            [(5, 5)],
        )

        self.assertEqual(
            resultado,
            "rival_bot",
        )

    def test_serpientes_misma_longitud(self):
        renderer = object.__new__(VisualizadorPygame)

        resultado = renderer._obtener_serpiente_pequena(
            [(1, 1), (2, 1)],
            [(5, 5), (6, 5)],
        )

        self.assertIsNone(resultado)

    def test_una_serpiente_vacia(self):
        renderer = object.__new__(VisualizadorPygame)

        resultado = renderer._obtener_serpiente_pequena(
            [],
            [(5, 5)],
        )

        self.assertIsNone(resultado)

    def test_ambas_serpientes_vacias(self):
        renderer = object.__new__(VisualizadorPygame)

        resultado = renderer._obtener_serpiente_pequena(
            [],
            [],
        )

        self.assertIsNone(resultado)

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_renderizar_maneja_eventos(
        self,
        mock_pygame,
    ):
        mock_screen = MagicMock()
        mock_pygame.display.set_mode.return_value = mock_screen
        mock_pygame.event.get.return_value = []

        renderer = VisualizadorPygame()

        renderer.renderizar({
            "apple": None,
            "dev_sentinel": [],
            "rival_bot": [],
        })

        mock_pygame.event.get.assert_called_once()

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_cerrar_pygame(
        self,
        mock_pygame,
    ):
        mock_pygame.display.set_mode.return_value = MagicMock()

        renderer = VisualizadorPygame()

        renderer.cerrar()

        mock_pygame.quit.assert_called_once()

    @patch("BOT.dev_sentinel.renderer.pygame")
    def test_evento_quit_cierra_pygame(
        self,
        mock_pygame,
    ):
        mock_screen = MagicMock()
        mock_pygame.display.set_mode.return_value = mock_screen

        quit_event = MagicMock()
        quit_event.type = mock_pygame.QUIT

        mock_pygame.event.get.return_value = [
            quit_event
        ]

        renderer = VisualizadorPygame()

        with self.assertRaises(SystemExit):
            renderer.renderizar({
                "apple": None,
                "dev_sentinel": [],
                "rival_bot": [],
            })

        mock_pygame.quit.assert_called_once()


if __name__ == "__main__":
    unittest.main()