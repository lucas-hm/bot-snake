
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


if __name__ == "__main__":
    unittest.main()