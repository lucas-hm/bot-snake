import unittest
from unittest.mock import patch

import game_engine
from game_engine import GameMoveTool


class TestGameEngineCoverage(unittest.TestCase):

    def setUp(self):
        self.tool = GameMoveTool()

    def test_property_name(self):
        """Cubre la propiedad name."""
        self.assertEqual(self.tool.name, "calculate_move")

    def test_line_20_ascii_board_parsing(self):
        """Cubre la línea 20: cuando el parámetro 'board' es un string ASCII."""
        with patch.object(self.tool, "_parse_ascii_board") as mock_parse:
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
        self.assertEqual(res.metadata["strategy"], "no_body_found")  # type: ignore

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
        self.assertEqual(res.metadata["strategy"], "emergency_no_moves")  # type: ignore

    def test_discard_move_due_to_flood_fill_space(self):
        """Cubre el descarte por espacio en Flood Fill."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                # Cuerpo de tamaño 4
                "my_body": [[1, 1], [1, 2], [1, 3], [1, 4]],
                "enemy_body": [],
                "foods": [],
            },
        }
        res = self.tool.execute(payload)
        self.assertTrue(res.success)

    def test_auxiliary_bfs_and_flood_fill_methods(self):
        """Cubre los métodos de búsqueda e inundación auxiliares en la clase."""
        obstacles = {(1, 1)}

        # Probar BFS Distance Map
        dist_map = self.tool._get_bfs_distance_map((0, 0), obstacles, 3, 3)
        self.assertIn((0, 0), dist_map)

        # Probar BFS Distance Fast (Líneas 167-179)
        dist = self.tool._bfs_distance_fast((0, 0), (2, 2), obstacles, 3, 3)
        self.assertEqual(dist, 4)

        # Probar Flood Fill
        space = self.tool._flood_fill((0, 0), obstacles, 3, 3)
        self.assertEqual(space, 8)


if __name__ == "__main__":
    unittest.main()