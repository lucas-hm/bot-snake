"""Rules and scoring for the Snake game."""

class GameRules:
    """Define the rules and scoring of a Snake game."""

    FOOD_SCORE = 100
    SURVIVAL_SCORE = 1
    DEATH_SCORE = -500
    OPPONENT_WIN_SCORE = 1000
    FOOD_SYMBOL = "*"

    def __init__(self, max_moves: int):
        """Initialize the game rules.

        Args:
            max_moves: Maximum number of moves in the game.
        """
        self.max_moves = max_moves

    def get_food_score(self) -> int:
        """Return the score awarded for eating food."""
        return self.FOOD_SCORE

    def get_survival_score(self) -> int:
        """Return the score awarded for surviving a move."""
        return self.SURVIVAL_SCORE

    def get_death_score(self) -> int:
        """Return the score lost when the snake dies."""
        return self.DEATH_SCORE

    def get_opponent_win_score(self) -> int:
        """Return the score awarded to the opponent when the snake dies."""
        return self.OPPONENT_WIN_SCORE

    def is_food(self, cell: str) -> bool:
        """Return whether a board cell contains food."""
        return cell == self.FOOD_SYMBOL

    def causes_death(
        self,
        hits_wall: bool,
        hits_own_body: bool,
        hits_opponent: bool,
    ) -> bool:
        """Return whether a move causes the snake to die."""
        return hits_wall or hits_own_body or hits_opponent

    def get_score_for_move(
        self,
        ate_food: bool,
        died: bool,
    ) -> int:
        """Return the score obtained for a move.

        Eating food awards food points.
        A surviving move awards survival points.
        A fatal move applies the death penalty.
        """
        if died:
            return self.DEATH_SCORE

        score = self.SURVIVAL_SCORE

        if ate_food:
            score += self.FOOD_SCORE

        return score

    def has_moves_remaining(self, moves_played: int) -> bool:
        """Return whether the game has moves remaining."""
        return moves_played < self.max_moves