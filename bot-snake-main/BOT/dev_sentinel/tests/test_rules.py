"""Tests for the Snake game rules."""

import unittest

from BOT.dev_sentinel.rules import GameRules


class TestGameRules(unittest.TestCase):
    """Test the GameRules class."""

    def setUp(self):
        """Create a GameRules instance for each test."""
        self.rules = GameRules(max_moves=100)

    def test_initialization(self):
        """GameRules stores the maximum number of moves."""
        self.assertEqual(self.rules.max_moves, 100)

    def test_get_food_score(self):
        """Eating food awards 100 points."""
        self.assertEqual(self.rules.get_food_score(), 100)

    def test_get_survival_score(self):
        """Surviving a move awards 1 point."""
        self.assertEqual(self.rules.get_survival_score(), 1)

    def test_get_death_score(self):
        """Dying causes a 500-point penalty."""
        self.assertEqual(self.rules.get_death_score(), -500)

    def test_get_opponent_win_score(self):
        """The opponent receives 1000 points when the snake dies."""
        self.assertEqual(self.rules.get_opponent_win_score(), 1000)

    def test_is_food_returns_true_for_food_symbol(self):
        """The food symbol is recognized as food."""
        self.assertTrue(self.rules.is_food("*"))

    def test_is_food_returns_false_for_other_symbols(self):
        """Other symbols are not recognized as food."""
        self.assertFalse(self.rules.is_food("."))

    def test_causes_death_when_hitting_wall(self):
        """Hitting a wall causes death."""
        self.assertTrue(
            self.rules.causes_death(
                hits_wall=True,
                hits_own_body=False,
                hits_opponent=False,
            )
        )

    def test_causes_death_when_hitting_own_body(self):
        """Hitting the snake's own body causes death."""
        self.assertTrue(
            self.rules.causes_death(
                hits_wall=False,
                hits_own_body=True,
                hits_opponent=False,
            )
        )

    def test_causes_death_when_hitting_opponent(self):
        """Hitting the opponent causes death."""
        self.assertTrue(
            self.rules.causes_death(
                hits_wall=False,
                hits_own_body=False,
                hits_opponent=True,
            )
        )

    def test_causes_death_returns_false_when_no_collision(self):
        """A move without collisions does not cause death."""
        self.assertFalse(
            self.rules.causes_death(
                hits_wall=False,
                hits_own_body=False,
                hits_opponent=False,
            )
        )

    def test_get_score_for_move_when_dying(self):
        """A fatal move gives a -500 score."""
        self.assertEqual(
            self.rules.get_score_for_move(
                ate_food=False,
                died=True,
            ),
            -500,
        )

    def test_get_score_for_surviving_move(self):
        """A surviving move gives 1 point."""
        self.assertEqual(
            self.rules.get_score_for_move(
                ate_food=False,
                died=False,
            ),
            1,
        )

    def test_get_score_for_eating_food(self):
        """Eating food while surviving gives 101 points."""
        self.assertEqual(
            self.rules.get_score_for_move(
                ate_food=True,
                died=False,
            ),
            101,
        )

    def test_has_moves_remaining(self):
        """Returns true while moves remain."""
        self.assertTrue(self.rules.has_moves_remaining(99))

    def test_has_no_moves_remaining(self):
        """Returns false when the maximum number of moves is reached."""
        self.assertFalse(self.rules.has_moves_remaining(100))

    def test_has_no_moves_remaining_after_limit(self):
        """Returns false after the maximum number of moves is exceeded."""
        self.assertFalse(self.rules.has_moves_remaining(101))


if __name__ == "__main__":
    unittest.main()