
import unittest
from unittest.mock import patch

import BOT.dev_sentinel.game_engine as game_engine
from BOT.dev_sentinel import game_engine

class TestGameEngineCoverage(unittest.TestCase):

    def setUp(self):
        self.tool = game_engine.GameMoveTool()

    def test_property_name(self):
        """Cubre la propiedad name."""
        self.assertEqual(self.tool.name, "calculate_move")

    def test_line_20_ascii_board_parsing(self):
        """Cubre la línea 20: cuando board es un string ASCII."""
        with patch.object(
            self.tool,
            "_parse_ascii_board",
            create=True,
        ) as mock_parse:

            payload = {
                "game_id": "g1",
                "turn_token": "t1",
                "board": "|---|---|---|",
                "side": "A",
            }

            res = self.tool.execute(payload)

            self.assertTrue(res.success)
            mock_parse.assert_called_once_with(
                "|---|---|---|",
                "A",
            )

    def test_line_35_no_my_body(self):
        """Cubre el caso donde my_body_list está vacío."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "board": {
                "my_body": [],
                "enemy_body": [],
                "foods": [],
            },
        }

        res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertEqual(
            res.metadata["strategy"], # type: ignore
            "no_body_found",
        )

    def test_line_52_enemy_head_on_food(self):
        """Cubre el caso donde la cabeza enemiga está sobre comida."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2], [2, 1]],
                "enemy_body": [[0, 0], [0, 1]],
                "foods": [[0, 0]],
            },
        }

        res = self.tool.execute(payload)

        self.assertTrue(res.success)

    def test_enemy_body_without_food(self):
        """
        Cubre la rama:

            if enemy_body_list and not enemy_will_eat:
                enemy_obstacles = ...

        Es decir, existe enemigo pero su cabeza no está
        sobre una comida.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2], [2, 3]],
                "enemy_body": [[4, 4], [4, 3]],
                "foods": [],
            },
        }

        res = self.tool.execute(payload)

        self.assertTrue(res.success)

    def test_lines_84_86_emergency_no_moves(self):
        """
        Cubre el caso emergency_no_moves.

        Se fuerza una situación donde todos los movimientos
        inmediatos están bloqueados.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 3,
            "rows": 3,
            "board": {
                "my_body": [[1, 1], [1, 0]],
                "enemy_body": [
                    [1, 2],
                    [0, 1],
                    [2, 1],
                ],
                "foods": [],
            },
        }

        with patch.object(
            game_engine, # type: ignore
            "choice",
            return_value="UP",
        ):
            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertEqual(
            res.metadata["strategy"], # type: ignore
            "emergency_no_moves",
        )
        self.assertEqual(
            res.output["direction"],
            "UP",
        )

    def test_food_directly_ahead(self):
        """
        Cubre:

            if target in food_positions:
                score += 100.0

        La comida está directamente arriba de la cabeza.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2]],
                "enemy_body": [],
                "foods": [[2, 1]],
            },
        }

        res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertEqual(
            res.output["direction"],
            "UP",
        )

    def test_food_distance_uses_bfs(self):
        """
        Cubre la rama donde target no es directamente comida
        y se llama a _bfs_distance_fast().
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 10,
            "rows": 10,
            "board": {
                "my_body": [[1, 1]],
                "enemy_body": [],
                "foods": [[5, 5]],
            },
        }

        with patch.object(
            self.tool,
            "_bfs_distance_fast",
            wraps=self.tool._bfs_distance_fast,
        ) as mock_bfs:
            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertTrue(mock_bfs.called)

    def test_food_distance_infinite_uses_manhattan(self):
        """
        Cubre:

            if food_dist_from_target == float("inf"):
                food_dist_from_target = Manhattan

        Se fuerza _bfs_distance_fast() para que no encuentre
        una ruta.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2]],
                "enemy_body": [],
                "foods": [[4, 4]],
            },
        }

        with patch.object(
            self.tool,
            "_bfs_distance_fast",
            return_value=float("inf"),
        ) as mock_bfs:

            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertTrue(mock_bfs.called)

    def test_discard_move_due_to_flood_fill_space(self):
        """
        Cubre:

            if space_after < required_space and len(valid_moves) > 1:
                continue
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [
                    [1, 1],
                    [1, 2],
                    [1, 3],
                    [1, 4],
                ],
                "enemy_body": [],
                "foods": [],
            },
        }

        with patch.object(
            self.tool,
            "_flood_fill",
            return_value=0,
        ) as mock_flood:

            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertTrue(mock_flood.called)

    def test_get_bfs_distance_map(self):
        """Prueba BFS con obstáculos."""
        obstacles = {(1, 1)}

        dist_map = self.tool._get_bfs_distance_map(
            (0, 0),
            obstacles,
            3,
            3,
        )

        self.assertIn((0, 0), dist_map)
        self.assertNotIn((1, 1), dist_map)

        # Debe poder rodear el obstáculo.
        self.assertIn((2, 2), dist_map)

    def test_get_bfs_distance_map_boundaries(self):
        """
        Cubre los límites del tablero.

        En un tablero 1x1 no existen vecinos válidos.
        """
        dist_map = self.tool._get_bfs_distance_map(
            (0, 0),
            set(),
            1,
            1,
        )

        self.assertEqual(
            dist_map,
            {(0, 0): 0},
        )

    def test_bfs_distance_fast_reaches_target(self):
        """
        Cubre:

            if curr == target:
                return float(dist)
        """
        dist = self.tool._bfs_distance_fast(
            (0, 0),
            (2, 2),
            set(),
            3,
            3,
        )

        self.assertEqual(
            dist,
            4.0,
        )

    def test_bfs_distance_fast_returns_infinity(self):
        """
        Cubre:

            return float("inf")

        Se bloquea completamente el acceso al objetivo.
        """
        obstacles = {
            (1, 0),
            (0, 1),
            (1, 1),
            (2, 1),
        }

        dist = self.tool._bfs_distance_fast(
            (0, 0),
            (2, 0),
            obstacles,
            3,
            3,
        )

        self.assertEqual(
            dist,
            float("inf"),
        )

    def test_flood_fill_counts_reachable_cells(self):
        """Cubre el recorrido normal del Flood Fill."""
        obstacles = {(1, 1)}

        space = self.tool._flood_fill(
            (0, 0),
            obstacles,
            3,
            3,
        )

        self.assertEqual(
            space,
            8,
        )

    def test_flood_fill_single_cell(self):
        """Cubre el caso mínimo del Flood Fill."""
        space = self.tool._flood_fill(
            (0, 0),
            set(),
            1,
            1,
        )

        self.assertEqual(
            space,
            1,
        )

    def test_flood_fill_with_many_obstacles(self):
        """
        Cubre el comportamiento del Flood Fill cuando
        prácticamente todo el tablero está bloqueado.
        """
        obstacles = {
            (1, 0),
            (0, 1),
            (1, 1),
            (2, 0),
            (2, 1),
            (0, 2),
            (1, 2),
        }

        space = self.tool._flood_fill(
            (0, 0),
            obstacles,
            3,
            3,
        )

        self.assertEqual(
            space,
            1,
        )

if __name__ == "__main__":
    unittest.main()