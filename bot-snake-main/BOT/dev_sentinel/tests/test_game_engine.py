import unittest
from unittest.mock import patch

from BOT.dev_sentinel.game_engine import GameMoveTool, MCTSNode, HeadToHeadMCTS


class TestMCTSNode(unittest.TestCase):
    """Tests for MCTSNode."""

    def test_is_fully_expanded_false(self):
        node = MCTSNode(
            my_head=(2, 2),
            enemy_head=None,
            obstacles=set(),
        )

        self.assertFalse(node.is_fully_expanded())

    def test_is_fully_expanded_true(self):
        node = MCTSNode(
            my_head=(2, 2),
            enemy_head=None,
            obstacles=set(),
        )

        node.children = [object(), object(), object(), object()]

        self.assertTrue(node.is_fully_expanded())


class TestHeadToHeadMCTS(unittest.TestCase):
    """Tests for HeadToHeadMCTS."""

    def setUp(self):
        self.mcts = HeadToHeadMCTS(
            width=10,
            height=10,
            iterations=1,
        )

    def test_is_terminal_outside_left(self):
        node = MCTSNode(
            my_head=(-1, 5),
            enemy_head=None,
            obstacles=set(),
        )

        self.assertTrue(self.mcts._is_terminal(node))

    def test_is_terminal_outside_right(self):
        node = MCTSNode(
            my_head=(10, 5),
            enemy_head=None,
            obstacles=set(),
        )

        self.assertTrue(self.mcts._is_terminal(node))

    def test_is_terminal_outside_top(self):
        node = MCTSNode(
            my_head=(5, -1),
            enemy_head=None,
            obstacles=set(),
        )

        self.assertTrue(self.mcts._is_terminal(node))

    def test_is_terminal_outside_bottom(self):
        node = MCTSNode(
            my_head=(5, 10),
            enemy_head=None,
            obstacles=set(),
        )

        self.assertTrue(self.mcts._is_terminal(node))

    def test_is_terminal_obstacle(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles={(5, 5)},
        )

        self.assertTrue(self.mcts._is_terminal(node))

    def test_is_terminal_valid_position(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles=set(),
        )

        self.assertFalse(self.mcts._is_terminal(node))

    def test_search_without_valid_moves_returns_none(self):
        result = self.mcts.search(
            my_head=(5, 5),
            enemy_head=(7, 7),
            obstacles=set(),
            valid_moves={},
        )

        self.assertIsNone(result)

    def test_expand_creates_child(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=(7, 7),
            obstacles={(3, 3)},
        )

        child = self.mcts._expand(node)

        self.assertEqual(len(node.children), 1)
        self.assertIs(child.parent, node)
        self.assertIn(child.move_from_parent, self.mcts.dirs)
        self.assertIn((5, 5), child.obstacles)
        self.assertEqual(child.enemy_head, (7, 7))

    def test_expand_uses_untried_move(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles=set(),
        )

        node.children = [
            MCTSNode(
                my_head=(5, 4),
                enemy_head=None,
                obstacles=set(),
                parent=node,
                move_from_parent="UP",
            )
        ]

        child = self.mcts._expand(node)

        self.assertNotEqual(child.move_from_parent, "UP")

    def test_select_expands_unexpanded_node(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles=set(),
        )

        selected = self.mcts._select(node)

        self.assertIs(selected.parent, node)
        self.assertEqual(len(node.children), 1)

    def test_select_returns_terminal_node(self):
        node = MCTSNode(
            my_head=(-1, 5),
            enemy_head=None,
            obstacles=set(),
        )

        selected = self.mcts._select(node)

        self.assertIs(selected, node)

    def test_best_uct_returns_child(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles=set(),
        )
        node.visits = 10

        child_one = MCTSNode(
            my_head=(5, 4),
            enemy_head=None,
            obstacles=set(),
            parent=node,
            move_from_parent="UP",
        )
        child_one.visits = 5
        child_one.value = 10.0

        child_two = MCTSNode(
            my_head=(5, 6),
            enemy_head=None,
            obstacles=set(),
            parent=node,
            move_from_parent="DOWN",
        )
        child_two.visits = 1
        child_two.value = 10.0

        node.children = [child_one, child_two]

        result = self.mcts._best_uct(node)

        self.assertIn(result, node.children)

    def test_rollout_immediate_loss_outside_board(self):
        node = MCTSNode(
            my_head=(-1, 0),
            enemy_head=None,
            obstacles=set(),
        )

        result = self.mcts._rollout(node)

        self.assertEqual(result, -1.0)

    def test_rollout_immediate_loss_on_obstacle(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles={(5, 5)},
        )

        result = self.mcts._rollout(node)

        self.assertEqual(result, -1.0)

    def test_rollout_without_enemy_survives(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles=set(),
        )

        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            result = self.mcts._rollout(node)

        self.assertEqual(result, 1.0)

    def test_rollout_with_enemy(self):
        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=(7, 7),
            obstacles=set(),
        )

        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            result = self.mcts._rollout(node)

        self.assertEqual(result, 1.0)

    def test_rollout_enemy_has_no_valid_moves(self):
        obstacles = {
            (6, 7),
            (8, 7),
            (7, 6),
            (7, 8),
        }

        node = MCTSNode(
            my_head=(2, 2),
            enemy_head=(7, 7),
            obstacles=obstacles,
        )

        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            result = self.mcts._rollout(node)

        self.assertEqual(result, 1.0)

    def test_rollout_my_snake_has_no_valid_moves(self):
        obstacles = {
            (4, 5),
            (6, 5),
            (5, 4),
            (5, 6),
        }

        node = MCTSNode(
            my_head=(5, 5),
            enemy_head=None,
            obstacles=obstacles,
        )

        result = self.mcts._rollout(node)

        self.assertEqual(result, -1.0)

    def test_search_returns_selected_move(self):
        mcts = HeadToHeadMCTS(
            width=10,
            height=10,
            iterations=3,
        )

        valid_moves = {
            "UP": (5, 4),
            "DOWN": (5, 6),
        }

        with patch(
            "BOT.dev_sentinel.game_engine.random.choice",
            side_effect=lambda values: values[0],
        ):
            result = mcts.search(
                my_head=(5, 5),
                enemy_head=(8, 8),
                obstacles=set(),
                valid_moves=valid_moves,
            )

        self.assertIn(result, {"UP", "DOWN", "LEFT", "RIGHT"})


class TestGameMoveTool(unittest.TestCase):
    """Tests for GameMoveTool."""

    def setUp(self):
        self.tool = GameMoveTool()

    def make_data(
        self,
        my_body,
        enemy_body=None,
        foods=None,
        cols=10,
        rows=10,
    ):
        return {
            "game_id": "test-game",
            "turn_token": "test-token",
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

    def test_execute_without_body(self):
        data = self.make_data(
            my_body=[],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(result.output["direction"], "RIGHT")
        self.assertEqual(result.metadata["strategy"], "no_body_found") # type: ignore

    def test_execute_single_segment(self):
        data = self.make_data(
            my_body=[(5, 5)],
            foods=[(6, 5)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(result.output["direction"], "RIGHT")
        self.assertEqual(result.output["row"], 6)
        self.assertEqual(result.output["col"], 5)
        self.assertEqual(
            result.metadata["strategy"], # type: ignore
            "BFS_Active_Strategy",
        )

    def test_execute_body_moving_right_forbids_left(self):
        data = self.make_data(
            my_body=[
                (5, 5),
                (4, 5),
                (3, 5),
            ],
            foods=[(5, 4)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertNotEqual(result.output["direction"], "LEFT")

    def test_execute_body_moving_left_forbids_right(self):
        data = self.make_data(
            my_body=[
                (4, 5),
                (5, 5),
                (6, 5),
            ],
            foods=[(4, 4)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertNotEqual(result.output["direction"], "RIGHT")

    def test_execute_body_moving_down_forbids_up(self):
        data = self.make_data(
            my_body=[
                (5, 5),
                (5, 4),
                (5, 3),
            ],
            foods=[(6, 5)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertNotEqual(result.output["direction"], "UP")

    def test_execute_body_moving_up_forbids_down(self):
        data = self.make_data(
            my_body=[
                (5, 5),
                (5, 6),
                (5, 7),
            ],
            foods=[(6, 5)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertNotEqual(result.output["direction"], "DOWN")

    def test_execute_enemy_not_eating(self):
        data = self.make_data(
            my_body=[(2, 2), (2, 3)],
            enemy_body=[(8, 8), (8, 7)],
            foods=[(1, 1)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)

    def test_execute_enemy_eating(self):
        data = self.make_data(
            my_body=[(2, 2), (2, 3)],
            enemy_body=[(8, 8), (8, 7)],
            foods=[(8, 8), (1, 1)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)

    def test_execute_emergency_no_moves(self):
        data = self.make_data(
            my_body=[(1, 1)],
            enemy_body=[
                (0, 1),
                (2, 1),
                (1, 0),
                (1, 2),
            ],
        )

        with patch(
            "BOT.dev_sentinel.game_engine.choice",
            return_value="UP",
        ):
            result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(result.output["direction"], "UP")
        self.assertEqual(
            result.metadata["strategy"], # type: ignore
            "emergency_no_moves",
        )

    def test_execute_mcts_combat_strategy(self):
        data = self.make_data(
            my_body=[(4, 5)],
            enemy_body=[(6, 5)],
            foods=[],
        )

        with patch(
            "BOT.dev_sentinel.game_engine.HeadToHeadMCTS.search",
            return_value="RIGHT",
        ):
            result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(result.output["direction"], "RIGHT")
        self.assertEqual(result.output["row"], 5)
        self.assertEqual(result.output["col"], 5)
        self.assertEqual(
            result.metadata["strategy"], # type: ignore
            "MCTS_Combat_Tactics",
        )

    def test_execute_mcts_invalid_move_falls_back_to_bfs(self):
        data = self.make_data(
            my_body=[(4, 5)],
            enemy_body=[(6, 5)],
            foods=[(4, 4)],
        )

        with patch(
            "BOT.dev_sentinel.game_engine.HeadToHeadMCTS.search",
            return_value="INVALID",
        ):
            result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(
            result.metadata["strategy"], # type: ignore
            "BFS_Active_Strategy",
        )

    def test_execute_food_is_preferred(self):
        data = self.make_data(
            my_body=[(5, 5)],
            foods=[(6, 5)],
        )

        result = self.tool.execute(data)

        self.assertEqual(result.output["direction"], "RIGHT")
        self.assertEqual(result.output["row"], 6)
        self.assertEqual(result.output["col"], 5)

    def test_execute_avoids_food_on_tail(self):
        data = self.make_data(
            my_body=[
                (5, 5),
                (5, 6),
                (5, 7),
            ],
            foods=[(5, 7)],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertNotEqual(
            result.output["direction"],
            "DOWN",
        )

    def test_execute_enemy_equal_length_avoids_head_neighbor(self):
        data = self.make_data(
            my_body=[
                (4, 5),
                (4, 6),
            ],
            enemy_body=[
                (6, 5),
                (6, 6),
            ],
            foods=[],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertNotEqual(result.output["direction"], "RIGHT")

    def test_execute_longer_snake_can_attack_enemy_neighbor(self):
        data = self.make_data(
            my_body=[
                (4, 5),
                (4, 6),
                (4, 7),
            ],
            enemy_body=[
                (6, 5),
                (6, 6),
            ],
            foods=[],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)

    def test_execute_with_cols_and_rows_override_board(self):
        data = self.make_data(
            my_body=[(2, 2)],
            foods=[(3, 2)],
            cols=5,
            rows=5,
        )
        data["board"]["width"] = 20
        data["board"]["height"] = 20

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(result.output["row"], 3)
        self.assertEqual(result.output["col"], 2)

    def test_execute_empty_food_uses_tail_heuristic(self):
        data = self.make_data(
            my_body=[
                (5, 5),
                (5, 6),
                (5, 7),
            ],
            foods=[],
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(
            result.metadata["strategy"], # type: ignore
            "BFS_Active_Strategy",
        )

    def test_execute_prefers_non_border_move_when_scores_allow(self):
        data = self.make_data(
            my_body=[(1, 1)],
            foods=[(2, 1)],
            cols=5,
            rows=5,
        )

        result = self.tool.execute(data)

        self.assertTrue(result.success)
        self.assertEqual(result.output["direction"], "RIGHT")


class TestGameMoveToolHelpers(unittest.TestCase):
    """Tests for GameMoveTool helper methods."""

    def setUp(self):
        self.tool = GameMoveTool()

    def test_get_bfs_distance_map(self):
        distances = self.tool._get_bfs_distance_map(
            start=(0, 0),
            obstacles={(1, 0)},
            width=3,
            height=3,
        )

        self.assertEqual(distances[(0, 0)], 0)
        self.assertNotIn((1, 0), distances)
        self.assertEqual(distances[(2, 0)], 4)
        self.assertEqual(distances[(2, 2)], 4)

    def test_bfs_distance_fast_reachable(self):
        distance = self.tool._bfs_distance_fast(
            start=(0, 0),
            target=(2, 0),
            obstacles={(1, 0)},
            width=3,
            height=3,
        )

        self.assertEqual(distance, 4.0)

    def test_bfs_distance_fast_unreachable(self):
        obstacles = {
            (1, 0),
            (0, 1),
            (1, 1),
        }

        distance = self.tool._bfs_distance_fast(
            start=(0, 0),
            target=(2, 2),
            obstacles=obstacles,
            width=3,
            height=3,
        )

        self.assertEqual(distance, float("inf"))

    def test_flood_fill(self):
        space = self.tool._flood_fill(
            start=(0, 0),
            obstacles={(1, 0)},
            width=3,
            height=3,
        )

        self.assertEqual(space, 8)

    def test_flood_fill_single_cell(self):
        space = self.tool._flood_fill(
            start=(1, 1),
            obstacles={
                (0, 1),
                (2, 1),
                (1, 0),
                (1, 2),
            },
            width=3,
            height=3,
        )

        self.assertEqual(space, 1)

    def test_bfs_distance_start_equals_target(self):
        distance = self.tool._bfs_distance_fast(
            start=(2, 2),
            target=(2, 2),
            obstacles=set(),
            width=5,
            height=5,
        )

        self.assertEqual(distance, 0.0)


if __name__ == "__main__":
    unittest.main()