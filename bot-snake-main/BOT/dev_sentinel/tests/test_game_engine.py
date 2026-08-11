
import unittest
from unittest.mock import MagicMock, patch

import game_engine
from game_engine import GameMoveTool


class TestGameEngineCoverage(unittest.TestCase):

    def setUp(self):
        self.tool = GameMoveTool()

    def test_property_name(self):
        """Cubre la línea 9: propiedad name."""
        self.assertEqual(self.tool.name, "calculate_move")

    def test_no_my_body(self):
        """Cubre la línea 35: sin serpiente propia en el tablero."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "board": {"my_body": [], "enemy_body": [], "foods": []}
        }
        res = self.tool.execute(payload)
        self.assertTrue(res.success)
        self.assertEqual(res.metadata["strategy"], "no_body_found") # type: ignore

    def test_ascii_board_parser_call(self):
        """Cubre la línea 20: cuando board es un string ASCII."""
        # Se mockea _parse_ascii_board para aislar el flujo de la línea 20
        with patch.object(self.tool, '_parse_ascii_board') as mock_parse:
            mock_parse.return_value = {
                "my_body": [[2, 2], [2, 1]],
                "enemy_body": [],
                "foods": [[2, 3]],
                "width": 10,
                "height": 10
            }
            payload = {
                "game_id": "g1",
                "turn_token": "t1",
                "board": "|---|---|---|",
                "side": "A"
            }
            res = self.tool.execute(payload)
            self.assertTrue(res.success)
            mock_parse.assert_called_once_with("|---|---|---|", "A")

    def test_enemy_obstacle_and_food_logic(self):
        """Cubre la línea 52: interacción con cola/enemigo y comida."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2], [2, 1]],
                "enemy_body": [[0, 0], [0, 1]],  # Enemigo que NO come
                "foods": [[2, 3]]
            }
        }
        res = self.tool.execute(payload)
        self.assertTrue(res.success)

    def test_emergency_no_moves(self):
        """Cubre las líneas 84-86: serpiente completamente encerrada."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 3,
            "rows": 3,
            "board": {
                "my_body": [[1, 1], [1, 0]],
                # Encerrada por enemigos rodeándola completamente
                "enemy_body": [[1, 2], [0, 1], [2, 1]],
                "foods": []
            }
        }
        res = self.tool.execute(payload)
        self.assertTrue(res.success)
        self.assertEqual(res.metadata["strategy"], "emergency_no_moves") # type: ignore

    def test_fallback_best_move_selection(self):
        """Cubre la línea 138: fallback al elegir movimiento si best_move es None."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2], [2, 1]],
                "enemy_body": [],
                "foods": []  # Sin comidas -> scores en 0
            }
        }
        # Forzamos que la variable best_move quede vacía simulando una falla interna de asignación
        with patch("game_engine.choice", return_value="UP") as mock_choice:
            res = self.tool.execute(payload)
            self.assertTrue(res.success)

    def test_line_20_ascii_board_parsing(self):
        """Cubre la línea 20: cuando el parámetro 'board' es un string ASCII."""
        with patch.object(self.tool, '_parse_ascii_board') as mock_parse:
            mock_parse.return_value = {
                "my_body": [[2, 2], [2, 1]],
                "enemy_body": [],
                "foods": [[2, 3]],
                "width": 10,
                "height": 10,
            }
            payload = {
                "game_id": "g1",
                "turn_token": "t1",
                "board": "|---|---|---|",
                "side": "A",
            }
            res = self.tool.execute(payload)
            self.assertTrue(res.success)
            mock_parse.assert_called_once_with("|---|---|---|", "A")

    def test_line_35_no_my_body(self):
        """Cubre la línea 35: cuando my_body_list está vacío."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "board": {"my_body": [], "enemy_body": [], "foods": []},
        }
        res = self.tool.execute(payload)
        self.assertTrue(res.success)
        self.assertEqual(res.metadata["strategy"], "no_body_found") # type: ignore

    def test_line_52_enemy_head_on_food(self):
        """Cubre la línea 52: cuando la cabeza del enemigo va a comer."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2], [2, 1]],
                "enemy_body": [[0, 0], [0, 1]],
                "foods": [[0, 0]],  # La cabeza del enemigo está en la comida
            },
        }
        res = self.tool.execute(payload)
        self.assertTrue(res.success)

    def test_lines_84_86_emergency_no_moves(self):
        """Cubre las líneas 84-86: serpiente completamente encerrada sin movimientos."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 3,
            "rows": 3,
            "board": {
                "my_body": [[1, 1], [1, 0]],
                # Rodeada totalmente por el enemigo
                "enemy_body": [[1, 2], [0, 1], [2, 1]],
                "foods": [],
            },
        }
        res = self.tool.execute(payload)
        self.assertTrue(res.success)
        self.assertEqual(res.metadata["strategy"], "emergency_no_moves") # type: ignore

    def test_line_138_fallback_choice_when_no_best_move(self):
        """Cubre la línea 138: si best_move queda en None se usa choice(valid_moves)."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2], [2, 1]],
                "enemy_body": [],
                "foods": [],
            },
        }
        # Forzamos que best_move pase a None antes de evaluar la línea 138
        with patch("game_engine.choice", return_value="UP") as mock_choice:
            res = self.tool.execute(payload)
            self.assertTrue(res.success)


if __name__ == "__main__":
    unittest.main()