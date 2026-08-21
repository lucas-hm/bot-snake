import unittest
from unittest.mock import patch

from BOT.dev_sentinel.game_engine import GameMoveTool, HeadToHeadMCTS, MCTSNode

class TestMCTSNode(unittest.TestCase):
    def test_not_fully_expanded(self):
        node = MCTSNode((2, 2), None, set())
        self.assertFalse(node.is_fully_expanded())

    def test_fully_expanded(self):
        node = MCTSNode((2, 2), None, set())
        node.children = [object()] * 4
        self.assertTrue(node.is_fully_expanded())


class TestHeadToHeadMCTS(unittest.TestCase):
    def setUp(self):
        self.mcts = HeadToHeadMCTS(10, 10, iterations=3)

    def test_terminal_out_of_bounds(self):
        for head in [(-1, 0), (10, 0), (0, -1), (0, 10)]:
            node = MCTSNode(head, None, set())
            self.assertTrue(self.mcts._is_terminal(node))

    def test_terminal_obstacle(self):
        node = MCTSNode((5, 5), None, {(5, 5)})
        self.assertTrue(self.mcts._is_terminal(node))

    def test_non_terminal(self):
        node = MCTSNode((5, 5), None, set())
        self.assertFalse(self.mcts._is_terminal(node))

    def test_search_empty_moves(self):
        self.assertIsNone(
            self.mcts.search((5, 5), (8, 8), set(), {})
        )

    def test_expand(self):
        node = MCTSNode((5, 5), (8, 8), {(2, 2)})
        child = self.mcts._expand(node)

        self.assertIs(child.parent, node)
        self.assertEqual(len(node.children), 1)
        self.assertIn(child.move_from_parent, self.mcts.dirs)
        self.assertIn((5, 5), child.obstacles)

    def test_expand_skips_tried_move(self):
        node = MCTSNode((5, 5), None, set())
        node.children.append(
            MCTSNode(
                (5, 4),
                None,
                set(),
                parent=node,
                move_from_parent="UP",
            )
        )
        child = self.mcts._expand(node)
        self.assertNotEqual(child.move_from_parent, "UP")

    def test_select_expands_node(self):
        node = MCTSNode((5, 5), None, set())
        result = self.mcts._select(node)
        self.assertIs(result.parent, node)

    def test_select_terminal_node(self):
        node = MCTSNode((-1, 5), None, set())
        self.assertIs(self.mcts._select(node), node)

    def test_best_uct(self):
        node = MCTSNode((5, 5), None, set())
        node.visits = 10

        first = MCTSNode(
            (5, 4), None, set(), parent=node, move_from_parent="UP"
        )
        first.visits = 5
        first.value = 10

        second = MCTSNode(
            (5, 6), None, set(), parent=node, move_from_parent="DOWN"
        )
        second.visits = 1
        second.value = 1

        node.children = [first, second]
        self.assertIn(self.mcts._best_uct(node), node.children)

    def test_rollout_out_of_bounds(self):
        node = MCTSNode((-1, 5), None, set())
        self.assertEqual(self.mcts._rollout(node), -1.0)

    def test_rollout_obstacle(self):
        node = MCTSNode((5, 5), None, {(5, 5)})
        self.assertEqual(self.mcts._rollout(node), -1.0)

    def test_rollout_no_enemy_survives(self):
        node = MCTSNode((5, 5), None, set())
        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            self.assertEqual(self.mcts._rollout(node), 1.0)

    def test_rollout_enemy_moves(self):
        node = MCTSNode((5, 5), (7, 7), set())
        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            self.assertEqual(self.mcts._rollout(node), 1.0)

    def test_rollout_enemy_trapped(self):
        obstacles = {(6, 7), (8, 7), (7, 6), (7, 8)}
        node = MCTSNode((2, 2), (7, 7), obstacles)
        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            self.assertEqual(self.mcts._rollout(node), 1.0)

    def test_rollout_my_snake_trapped(self):
        obstacles = {(4, 5), (6, 5), (5, 4), (5, 6)}
        node = MCTSNode((5, 5), None, obstacles)
        self.assertEqual(self.mcts._rollout(node), -1.0)

    def test_backpropagate(self):
        root = MCTSNode((5, 5), None, set())
        child = MCTSNode(
            (5, 4), None, set(), parent=root, move_from_parent="UP"
        )
        grandchild = MCTSNode(
            (5, 3), None, set(), parent=child, move_from_parent="UP"
        )

        self.mcts._backpropagate(grandchild, 1.5)

        self.assertEqual(grandchild.visits, 1)
        self.assertEqual(child.visits, 1)
        self.assertEqual(root.visits, 1)
        self.assertEqual(root.value, 1.5)

    def test_search_returns_move(self):
        valid_moves = {"UP": (5, 4), "DOWN": (5, 6)}
        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            result = self.mcts.search(
                (5, 5), (8, 8), set(), valid_moves
            )

        self.assertIsNotNone(result)
        self.assertIn(result, self.mcts.dirs)


class TestGameMoveTool(unittest.TestCase):
    def setUp(self):
        self.tool = GameMoveTool()

    def data(self, my_body, enemy_body=None, foods=None, cols=10, rows=10):
        return {
            "game_id": "game",
            "turn_token": "token",
            "side": "A",
            "cols": cols,
            "rows": rows,
            "board": {
                "width": cols,
                "height": rows,
                "my_body": my_body,
                "enemy_body": enemy_body or [],
                "foods": foods or [],
            },
        }

    def test_name(self):
        self.assertEqual(self.tool.name, "calculate_move")

    def test_no_body(self):
        result = self.tool.execute(self.data([]))
        self.assertTrue(result.success)
        self.assertEqual(result.output["direction"], "RIGHT")
        self.assertEqual(result.metadata["strategy"], "no_body_found") # type: ignore

    def test_single_body_food(self):
        result = self.tool.execute(
            self.data([(5, 5)], foods=[(6, 5)])
        )
        self.assertTrue(result.success)
        self.assertEqual(result.output["direction"], "RIGHT")
        self.assertEqual(result.output["row"], 6)
        self.assertEqual(result.output["col"], 5)

    def test_forbidden_left(self):
        result = self.tool.execute(
            self.data([(5, 5), (4, 5), (3, 5)], foods=[(5, 4)])
        )
        self.assertNotEqual(result.output["direction"], "LEFT")

    def test_forbidden_right(self):
        result = self.tool.execute(
            self.data([(4, 5), (5, 5), (6, 5)], foods=[(4, 4)])
        )
        self.assertNotEqual(result.output["direction"], "RIGHT")

    def test_forbidden_up(self):
        result = self.tool.execute(
            self.data([(5, 5), (5, 4), (5, 3)], foods=[(6, 5)])
        )
        self.assertNotEqual(result.output["direction"], "UP")

    def test_forbidden_down(self):
        result = self.tool.execute(
            self.data([(5, 5), (5, 6), (5, 7)], foods=[(6, 5)])
        )
        self.assertNotEqual(result.output["direction"], "DOWN")

    def test_enemy_not_eating(self):
        result = self.tool.execute(
            self.data(
                [(2, 2), (2, 3)],
                enemy_body=[(8, 8), (8, 7)],
                foods=[(1, 1)],
            )
        )
        self.assertTrue(result.success)

    def test_enemy_eating(self):
        result = self.tool.execute(
            self.data(
                [(2, 2), (2, 3)],
                enemy_body=[(8, 8), (8, 7)],
                foods=[(8, 8)],
            )
        )
        self.assertTrue(result.success)

    def test_emergency_no_moves(self):
        result = self.tool.execute(
            self.data(
                [(0, 0)],
                enemy_body=[(1, 0), (0, 1), (2, 2)],
            )
        )
        self.assertTrue(result.success)
        self.assertEqual(result.metadata["strategy"], "emergency_no_moves") # type: ignore

    def test_mcts_combat(self):
        data = self.data([(4, 5)], enemy_body=[(6, 5)])
        with patch.object(
            HeadToHeadMCTS, "search", return_value="RIGHT"
        ):
            result = self.tool.execute(data)

        self.assertEqual(result.metadata["strategy"], "MCTS_Combat_Tactics") # type: ignore
        self.assertEqual(result.output["direction"], "RIGHT")
        self.assertEqual(result.output["row"], 5)
        self.assertEqual(result.output["col"], 5)

    def test_mcts_invalid_move_uses_bfs(self):
        data = self.data([(4, 5)], enemy_body=[(6, 5)], foods=[(4, 4)])
        with patch.object(
            HeadToHeadMCTS, "search", return_value="INVALID"
        ):
            result = self.tool.execute(data)

        self.assertEqual(result.metadata["strategy"], "BFS_Active_Strategy") # type: ignore

    def test_equal_length_avoids_enemy_neighbor(self):
        data = self.data(
            [(4, 5), (4, 6)],
            enemy_body=[(6, 5), (6, 6)],
        )
        with patch.object(HeadToHeadMCTS, "search", return_value=None):
            result = self.tool.execute(data)

        self.assertNotEqual(result.output["direction"], "RIGHT")

    def test_longer_can_attack(self):
        data = self.data(
            [(4, 5), (4, 6), (4, 7)],
            enemy_body=[(6, 5), (6, 6)],
        )
        with patch.object(HeadToHeadMCTS, "search", return_value=None):
            result = self.tool.execute(data)

        self.assertTrue(result.success)

    def test_tail_with_food_is_not_selected(self):
        data = self.data(
            [(5, 5), (5, 6), (5, 7)],
            foods=[(5, 7)],
        )
        result = self.tool.execute(data)
        self.assertNotEqual(result.output["direction"], "DOWN")

    def test_empty_food_uses_tail(self):
        result = self.tool.execute(
            self.data([(5, 5), (5, 6), (5, 7)])
        )
        self.assertEqual(
            result.metadata["strategy"], "BFS_Active_Strategy" # type: ignore
        )

    def test_board_dimensions_override(self):
        data = self.data([(2, 2)], foods=[(3, 2)], cols=5, rows=5)
        data["board"]["width"] = 20
        data["board"]["height"] = 20
        result = self.tool.execute(data)
        self.assertEqual(result.output["row"], 3)
        self.assertEqual(result.output["col"], 2)


class TestGameMoveToolHelpers(unittest.TestCase):
    def setUp(self):
        self.tool = GameMoveTool()

    def test_bfs_distance_map(self):
        distances = self.tool._get_bfs_distance_map(
            (0, 0), {(1, 0)}, 3, 3
        )
        self.assertEqual(distances[(0, 0)], 0)
        self.assertNotIn((1, 0), distances)
        self.assertEqual(distances[(2, 0)], 4)

    def test_bfs_fast_reachable(self):
        result = self.tool._bfs_distance_fast(
            (0, 0), (2, 0), {(1, 0)}, 3, 3
        )
        self.assertEqual(result, 4.0)

    def test_bfs_fast_unreachable(self):
        obstacles = {(1, 0), (0, 1), (1, 1)}
        result = self.tool._bfs_distance_fast(
            (0, 0), (2, 2), obstacles, 3, 3
        )
        self.assertEqual(result, float("inf"))

    def test_bfs_fast_same_position(self):
        result = self.tool._bfs_distance_fast(
            (2, 2), (2, 2), set(), 5, 5
        )
        self.assertEqual(result, 0.0)

    def test_flood_fill(self):
        result = self.tool._flood_fill(
            (0, 0), {(1, 0)}, 3, 3
        )
        self.assertEqual(result, 8)

    def test_flood_fill_single_cell(self):
        result = self.tool._flood_fill(
            (1, 1),
            {(0, 1), (2, 1), (1, 0), (1, 2)},
            3,
            3,
        )
        self.assertEqual(result, 1)


# =============================================================================
# Tests para las mejoras cirujanas (cambios 1-4)
# =============================================================================
class TestRolloutSemiGreedy(unittest.TestCase):
    """Cambio 3: el rollout semi-greedy prioriza espacio cuando greedy_bias > 0."""

    def setUp(self):
        self.mcts_greedy = HeadToHeadMCTS(10, 10, iterations=3, greedy_bias=0.7)
        self.mcts_random = HeadToHeadMCTS(10, 10, iterations=3, greedy_bias=0.0)

    def test_pick_my_rollout_greedy_elige_mas_espacio(self):
        # Desde (5,5) el movimiento UP (5,4) abre mas espacio que RIGHT (6,5)
        # porque (6,5),(7,5)... estan bloqueados por obstaculos a la derecha.
        obstacles = {(6, 5), (7, 5), (8, 5), (9, 5)}
        my_valid = [(5, 4), (6, 5)]
        # Forzamos greedy: random.random() < 0.7 siempre (mock).
        with patch(
            "BOT.dev_sentinel.game_engine.random.random",
            return_value=0.0,
        ):
            chosen = self.mcts_greedy._pick_my_rollout_move(
                (5, 5), my_valid, obstacles
            )
        self.assertEqual(chosen, (5, 4))

    def test_pick_my_rollout_random_cuando_bias_cero(self):
        # Con greedy_bias=0.0 siempre cae al random.choice.
        my_valid = [(5, 4), (6, 5)]
        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            return_value=(6, 5),
        ) as mock_choice:
            chosen = self.mcts_random._pick_my_rollout_move(
                (5, 5), my_valid, set()
            )
        mock_choice.assert_called_once_with(my_valid)
        self.assertEqual(chosen, (6, 5))

    def test_pick_my_rollout_random_falla_a_greedy(self):
        # greedy_bias alto pero random.random() >= bias -> cae a random.
        my_valid = [(5, 4), (6, 5)]
        with patch(
            "BOT.dev_sentinel.game_engine.random.random",
            return_value=0.9,  # >= 0.7, no greedy
        ), patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            return_value=(6, 5),
        ) as mock_choice:
            chosen = self.mcts_greedy._pick_my_rollout_move(
                (5, 5), my_valid, set()
            )
        mock_choice.assert_called_once()
        self.assertEqual(chosen, (6, 5))

    def test_rollout_greedy_sobrevive(self):
        # El rollout semi-greedy en un tablero abierto debe sobrevivir.
        node = MCTSNode((5, 5), None, set())
        with patch(
            "BOT.dev_sentinel.game_engine.random.random",
            return_value=0.0,  # siempre greedy
        ), patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            self.assertEqual(self.mcts_greedy._rollout(node), 1.0)


class TestEnemyProfileRollout(unittest.TestCase):
    """Cambio 4: el movimiento del rival en el rollout depende de su perfil."""

    def test_aggressive_elige_mas_cercano_a_mi(self):
        mcts = HeadToHeadMCTS(10, 10, iterations=3, enemy_profile="aggressive")
        # Enemigo en (1,1), mi cabeza en (5,5). Movimientos validos del
        # enemigo: (2,1) y (0,1). (2,1) esta mas cerca de (5,5).
        chosen = mcts._pick_enemy_rollout_move(
            (1, 1), (5, 5), [(2, 1), (0, 1)]
        )
        self.assertEqual(chosen, (2, 1))

    def test_non_aggressive_usa_random(self):
        mcts = HeadToHeadMCTS(10, 10, iterations=3, enemy_profile="random")
        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            return_value=(0, 1),
        ) as mock_choice:
            chosen = mcts._pick_enemy_rollout_move(
                (1, 1), (5, 5), [(2, 1), (0, 1)]
            )
        mock_choice.assert_called_once()
        self.assertEqual(chosen, (0, 1))

    def test_aggressive_sin_opciones_random(self):
        mcts = HeadToHeadMCTS(10, 10, iterations=3, enemy_profile="aggressive")
        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            return_value=(2, 1),
        ) as mock_choice:
            chosen = mcts._pick_enemy_rollout_move(
                (1, 1), (5, 5), []
            )
        mock_choice.assert_called_once_with([])
        self.assertEqual(chosen, (2, 1))

    def test_rollout_aggressive_sobrevive(self):
        mcts = HeadToHeadMCTS(
            10, 10, iterations=3, greedy_bias=0.0, enemy_profile="aggressive"
        )
        node = MCTSNode((5, 5), (7, 7), set())
        with patch(
            "BOT.dev_sentinel.game_engine.random.random",
            return_value=1.0,  # no greedy en mi movimiento
        ), patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            self.assertEqual(mcts._rollout(node), 1.0)


class TestCountEnemyExits(unittest.TestCase):
    """Cambio 2: helper que cuenta las salidas libres del enemigo."""

    def setUp(self):
        self.tool = GameMoveTool()

    def test_cuatro_salidas_centro(self):
        self.assertEqual(
            self.tool._count_enemy_exits((5, 5), set(), 10, 10),
            4,
        )

    def test_dos_salidas_esquina(self):
        # Esquina (0,0): solo DOWN y RIGHT estan libres.
        self.assertEqual(
            self.tool._count_enemy_exits((0, 0), set(), 10, 10),
            2,
        )

    def test_cero_salidas_acorralado(self):
        obstacles = {(1, 0), (0, 1)}
        self.assertEqual(
            self.tool._count_enemy_exits((0, 0), obstacles, 10, 10),
            0,
        )

    def test_una_salida(self):
        obstacles = {(6, 5), (4, 5), (5, 6)}
        self.assertEqual(
            self.tool._count_enemy_exits((5, 5), obstacles, 10, 10),
            1,
        )


class TestSkipMCTSTrivialEnemy(unittest.TestCase):
    """Cambio 2: si el enemigo esta acorralado (<=2 salidas) no se activa MCTS."""

    def setUp(self):
        self.tool = GameMoveTool()

    def data(self, my_body, enemy_body=None, foods=None, cols=10, rows=10):
        return {
            "game_id": "game",
            "turn_token": "token",
            "side": "A",
            "cols": cols,
            "rows": rows,
            "board": {
                "width": cols,
                "height": rows,
                "my_body": my_body,
                "enemy_body": enemy_body or [],
                "foods": foods or [],
            },
        }

    def test_mcts_no_se_usa_con_enemigo_acorralado(self):
        # Enemigo en (0,0) esquina = 2 salidas -> skip MCTS -> cae a BFS.
        # Mi cabeza en (2,0), distancia Manhattan = 2 (<=3, zona MCTS).
        with patch.object(
            HeadToHeadMCTS, "search", return_value="RIGHT"
        ) as mock_search:
            result = self.tool.execute(
                self.data([(2, 0)], enemy_body=[(0, 0)], foods=[(9, 9)])
            )
        # search nunca se llama porque el enemigo esta acorralado.
        mock_search.assert_not_called()
        self.assertEqual(result.metadata["strategy"], "BFS_Active_Strategy")


class TestAggressiveForaging(unittest.TestCase):
    """Cambio 1: cosechador agresivo prioriza comida cerca del enemigo."""

    def setUp(self):
        self.tool = GameMoveTool()

    def data(self, my_body, enemy_body=None, foods=None, cols=15, rows=15):
        return {
            "game_id": "game",
            "turn_token": "token",
            "side": "A",
            "cols": cols,
            "rows": rows,
            "board": {
                "width": cols,
                "height": rows,
                "my_body": my_body,
                "enemy_body": enemy_body or [],
                "foods": foods or [],
            },
        }

    def test_foraging_activo_cuando_enemigo_lejos(self):
        # Enemigo en (0,0), yo en (14,7). Distancia = 14 (>6).
        # Comida A en (13,7) cerca mia; comida B en (1,1) cerca del enemigo.
        # Con foraging agresivo, closest_food deberia ser B (cerca enemigo)
        # y alcanzable por nosotros antes o igual que el rival.
        result = self.tool.execute(
            self.data(
                [(14, 7)],
                enemy_body=[(0, 0)],
                foods=[(13, 7), (1, 1)],
            )
        )
        # Debe ejecutarse correctamente con BFS_Active_Strategy.
        self.assertTrue(result.success)
        self.assertEqual(result.metadata["strategy"], "BFS_Active_Strategy")

    def test_foraging_inactivo_cuando_enemigo_cerca(self):
        # Enemigo en (5,5), yo en (7,5). Distancia = 2 (<=6) -> no foraging.
        result = self.tool.execute(
            self.data(
                [(7, 5)],
                enemy_body=[(5, 5)],
                foods=[(8, 5), (4, 5)],
            )
        )
        self.assertTrue(result.success)


class TestEnemyProfileInference(unittest.TestCase):
    """Cambio 4: la inferencia del perfil del rival a partir del historial."""

    def setUp(self):
        self.tool = GameMoveTool()

    def test_perfil_inicia_unknown(self):
        self.assertEqual(self.tool._enemy_profile, "unknown")

    def test_perfil_sigue_unknown_con_pocas_muestras(self):
        # Menos de _profile_min_samples (4) muestras.
        for i in range(3):
            self.tool._update_enemy_profile((5, 5), (i, 0))
        self.assertEqual(self.tool._enemy_profile, "unknown")

    def test_perfil_aggressive_cuando_se_acerca(self):
        # El enemigo se acerca en todos los turnos -> aggressive.
        # Mi cabeza fija en (5,5). Enemigo va (8,5)->(7,5)->(6,5)->(5,5).
        positions = [(8, 5), (7, 5), (6, 5), (5, 5)]
        for ep in positions:
            self.tool._update_enemy_profile((5, 5), ep)
        self.assertEqual(self.tool._enemy_profile, "aggressive")

    def test_perfil_passive_cuando_no_se_acerca(self):
        # El enemigo se aleja -> passive.
        positions = [(5, 5), (6, 5), (7, 5), (8, 5)]
        for ep in positions:
            self.tool._update_enemy_profile((5, 5), ep)
        self.assertEqual(self.tool._enemy_profile, "passive")

    def test_perfil_ignora_enemy_head_none(self):
        self.tool._update_enemy_profile((5, 5), None)
        self.assertEqual(self.tool._enemy_profile, "unknown")
        self.assertEqual(self.tool._enemy_head_history, [])

    def test_perfil_ignora_my_head_none(self):
        self.tool._update_enemy_profile(None, (5, 5))
        self.assertEqual(self.tool._enemy_profile, "unknown")

    def test_historial_se_acota_a_20(self):
        for i in range(30):
            self.tool._update_enemy_profile((5, 5), (i % 10, 0))
        self.assertLessEqual(len(self.tool._enemy_head_history), 20)


class TestGameMoveToolInit(unittest.TestCase):
    """Verifica que GameMoveTool ahora tiene __init__ con estado de perfil."""

    def test_init_crea_estado_perfil(self):
        tool = GameMoveTool()
        self.assertEqual(tool._enemy_profile, "unknown")
        self.assertEqual(tool._enemy_head_history, [])
        self.assertEqual(tool._my_head_history, [])
        self.assertEqual(tool._profile_min_samples, 4)


if __name__ == "__main__":
    unittest.main()