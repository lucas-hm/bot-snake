import math
import unittest
from unittest.mock import MagicMock, patch

from BOT.dev_sentinel import game_engine  # type: ignore
from BOT.dev_sentinel.game_engine import HeadToHeadMCTS, MCTSNode  # type: ignore

class TestGameEngineCoverage(unittest.TestCase):
    def setUp(self):
        self.tool = game_engine.GameMoveTool()

    def test_property_name(self):
        """Cubre la propiedad name."""
        self.assertEqual(self.tool.name, "calculate_move")

    def test_line_20_ascii_board_parsing(self):
        """Cubre la línea 20: cuando board es un string ASCII."""
        mock_board_info = {
            "width": 5,
            "height": 5,
            "my_body": [[1, 1], [1, 0]],
            "enemy_body": [[3, 3]],
            "foods": [[2, 2]],
        }

        with patch.object(
            self.tool,
            "_parse_ascii_board",
            return_value=mock_board_info,
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

    def test_lines_84_86_emergency_no_moves(self):
        """Cubre el caso emergency_no_moves bloqueando todos los casilleros."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 3,
            "rows": 3,
            "board": {
                "my_body": [[0, 0], [0, 1]],
                "enemy_body": [[1, 0], [2, 0]],
                "foods": [],
            },
        }

        with patch(
            "BOT.dev_sentinel.game_engine.choice",
            return_value="UP",
        ):
            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        assert res.metadata is not None
        self.assertEqual(
            res.metadata.get("strategy"),
            "emergency_no_moves",
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
            res.metadata["strategy"],  # type: ignore
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
        Cubre la rama donde existe enemigo pero su cabeza
        no está sobre una comida.
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

    def test_food_directly_ahead(self):
        """
        Cubre el caso donde el movimiento elegido
        cae directamente sobre comida.
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
        Fuerza _bfs_distance_fast() a devolver infinito
        para cubrir el fallback Manhattan.
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
        Cubre el descarte de movimientos por falta de espacio.
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

    # ============================================================
    # NUEVOS TESTS - MONTE CARLO TREE SEARCH (MCTS)
    # ============================================================

    def test_mcts_combat_activation(self):
        """Verifica que MCTS se active si la distancia Manhattan al enemigo es <= 3."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 10,
            "rows": 10,
            "board": {
                "my_body": [[5, 5], [5, 6]],
                "enemy_body": [[5, 7], [5, 8]],  # Distancia = 2
                "foods": [],
            },
        }

        res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertEqual(res.metadata["strategy"], "MCTS_Combat_Tactics") # type: ignore

    def test_mcts_returns_none_fallback_to_bfs(self):
        """Si MCTS no encuentra movimiento, cae al flujo BFS estándar."""
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 10,
            "rows": 10,
            "board": {
                "my_body": [[5, 5], [5, 6]],
                "enemy_body": [[5, 7]],
                "foods": [],
            },
        }

        with patch.object(HeadToHeadMCTS, "search", return_value=None):
            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertEqual(res.metadata["strategy"], "BFS_Active_Strategy") # type: ignore

    def test_mcts_search_without_valid_moves(self):
        """Prueba HeadToHeadMCTS.search sin movimientos válidos."""
        mcts = HeadToHeadMCTS(10, 10)
        result = mcts.search((0, 0), (2, 2), set(), {})
        self.assertIsNone(result)

    def test_mcts_rollout_defeat_out_of_bounds_or_trapped(self):
        """Prueba las condiciones de derrota instantánea dentro del _rollout."""
        mcts = HeadToHeadMCTS(5, 5)
        node_out_of_bounds = MCTSNode((-1, 0), (2, 2), set())
        self.assertEqual(mcts._rollout(node_out_of_bounds), -1.0)

        # Sin movimientos válidos para mi serpiente
        obstacles = {(1, 0), (0, 1)}
        node_trapped = MCTSNode((0, 0), (4, 4), obstacles)
        self.assertEqual(mcts._rollout(node_trapped), -1.0)

    def test_mcts_uct_calculation(self):
        """Prueba la selección de nodo mediante UCT."""
        mcts = HeadToHeadMCTS(10, 10)
        parent = MCTSNode((5, 5), (5, 7), set())
        parent.visits = 10

        c1 = MCTSNode((5, 4), (5, 7), set(), parent=parent, move_from_parent="UP")
        c1.visits = 5
        c1.value = 2.0

        c2 = MCTSNode((5, 6), (5, 7), set(), parent=parent, move_from_parent="DOWN")
        c2.visits = 1
        c2.value = 0.0

        parent.children = [c1, c2]
        best = mcts._best_uct(parent)
        self.assertIn(best, [c1, c2])

    # ============================================================
    # TESTS DE HEURÍSTICAS Y CASOS BORDE
    # ============================================================

    def test_head_to_head_danger_is_discarded(self):
        """
        Verifica la heurística cabeza-cabeza.

        Si nuestra serpiente tiene una longitud menor o igual
        a la enemiga y un movimiento nos deja adyacentes a
        la cabeza enemiga, ese movimiento debe descartarse.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 7,
            "rows": 7,
            "board": {
                "my_body": [
                    [2, 2],
                ],
                "enemy_body": [
                    [6, 6],
                    [6, 5],
                    [6, 4],
                    [6, 3],
                    [6, 2],  # Enemigo lejos para evaluar la heurística BFS pura
                ],
                "foods": [],
            },
        }

        res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertEqual(res.metadata["strategy"], "BFS_Active_Strategy") # type: ignore

    def test_head_to_head_is_allowed_when_we_are_longer(self):
        """
        Verifica que una serpiente más larga que el enemigo
        pueda ejecutar un movimiento normalmente.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 7,
            "rows": 7,
            "board": {
                "my_body": [
                    [2, 2],
                    [2, 3],
                    [2, 4],
                ],
                "enemy_body": [
                    [6, 6],  # Lejos de MCTS
                ],
                "foods": [[2, 1]],
            },
        }

        res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertIn(
            res.output["direction"],
            ["UP", "DOWN", "LEFT", "RIGHT"],
        )

    def test_tail_chasing_when_no_food(self):
        """
        Verifica que, cuando no hay comida, la estrategia
        calcule la distancia hacia nuestra propia cola.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 10,
            "rows": 10,
            "board": {
                "my_body": [
                    [5, 5],
                    [5, 6],
                    [4, 6],
                    [4, 5],
                ],
                "enemy_body": [],
                "foods": [],
            },
        }

        original_bfs = self.tool._bfs_distance_fast

        with patch.object(
            self.tool,
            "_bfs_distance_fast",
            wraps=original_bfs,
        ) as mock_bfs:
            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertTrue(mock_bfs.called)
        self.assertEqual(
            res.output["direction"],
            "LEFT",
        )

    def test_wall_penalty_is_applied(self):
        """
        Verifica que una posición ubicada en un borde
        reciba el castigo de -10 puntos.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [[2, 2]],
                "enemy_body": [],
                "foods": [],
            },
        }

        with patch.object(
            self.tool,
            "_flood_fill",
            return_value=25,
        ):
            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertIn(
            res.output["direction"],
            ["UP", "DOWN", "LEFT", "RIGHT"],
        )

    def test_head_to_head_move_is_skipped_before_flood_fill(self):
        """
        Verifica que un movimiento cabeza-cabeza se descarte
        antes de ejecutar Flood Fill.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 7,
            "rows": 7,
            "board": {
                "my_body": [[2, 2]],
                "enemy_body": [[6, 6], [6, 5]],  # Fuera del rango de activación de MCTS
                "foods": [],
            },
        }

        with patch.object(
            self.tool,
            "_flood_fill",
            wraps=self.tool._flood_fill,
        ) as mock_flood:
            res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertLess(
            mock_flood.call_count,
            len(res.output),
        )

    def test_fallback_when_all_scored_moves_are_discarded(self):
        """
        Cubre el fallback cuando todos los movimientos puntuados son descartados.
        """
        payload = {
            "game_id": "g1",
            "turn_token": "t1",
            "cols": 5,
            "rows": 5,
            "board": {
                "my_body": [
                    [2, 2],
                    [2, 3],
                    [2, 4],
                ],
                "enemy_body": [],
                "foods": [],
            },
        }

        with patch.object(
            self.tool,
            "_flood_fill",
            return_value=0,
        ):
            with patch(
                "BOT.dev_sentinel.game_engine.choice",
                return_value="UP",
            ):
                res = self.tool.execute(payload)

        self.assertTrue(res.success)
        self.assertEqual(
            res.output["direction"],
            "UP",
        )

    # ============================================================
    # TESTS BFS
    # ============================================================

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
        self.assertIn((2, 2), dist_map)

    def test_get_bfs_distance_map_boundaries(self):
        """Cubre los límites del tablero."""
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
        """Cubre el caso donde BFS encuentra el objetivo."""
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
        """Cubre el caso donde BFS no puede llegar al objetivo."""
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

    # ============================================================
    # TESTS FLOOD FILL
    # ============================================================

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