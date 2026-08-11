import unittest
from game_engine import GameMoveTool


class TestStrategyScoring(unittest.TestCase):
    def setUp(self):
        self.engine = GameMoveTool()

    def test_score_move_prefers_aggressive_target_when_bot_has_advantage(self):
        attack_score = self.engine._score_move( # type: ignore
            move_name="UP",
            target=(5, 4),
            my_head=(5, 5),
            enemy_head=(8, 8),
            enemy_tail=(8, 8),
            food_positions={(7, 7)},
            obstacles=set(),
            grid_width=15,
            grid_height=15,
            my_body_len=5,
            enemy_body_len=3,
            is_aggressive=True,
            closest_food=(7, 7),
            attack_target=(5, 4),
            trap_targets=set(),
        )
        survival_score = self.engine._score_move( # type: ignore
            move_name="RIGHT",
            target=(6, 5),
            my_head=(5, 5),
            enemy_head=(8, 8),
            enemy_tail=(8, 8),
            food_positions={(7, 7)},
            obstacles=set(),
            grid_width=15,
            grid_height=15,
            my_body_len=5,
            enemy_body_len=3,
            is_aggressive=True,
            closest_food=(7, 7),
            attack_target=(8, 8),
            trap_targets=set(),
        )

        self.assertGreater(attack_score, survival_score)

    def test_score_move_penalizes_enemy_danger_zones(self):
        dangerous_score = self.engine._score_move( # type: ignore
            move_name="UP",
            target=(5, 4),
            my_head=(5, 5),
            enemy_head=(5, 4),
            enemy_tail=(8, 8),
            food_positions=set(),
            obstacles=set(),
            grid_width=15,
            grid_height=15,
            my_body_len=4,
            enemy_body_len=4,
            is_aggressive=False,
            closest_food=None,
            attack_target=None,
            trap_targets=set(),
        )
        safe_score = self.engine._score_move( # type: ignore
            move_name="RIGHT",
            target=(6, 5),
            my_head=(5, 5),
            enemy_head=(8, 8),
            enemy_tail=(8, 8),
            food_positions=set(),
            obstacles=set(),
            grid_width=15,
            grid_height=15,
            my_body_len=4,
            enemy_body_len=4,
            is_aggressive=False,
            closest_food=None,
            attack_target=None,
            trap_targets=set(),
        )

        self.assertGreater(safe_score, dangerous_score)


if __name__ == "__main__":
    unittest.main()
