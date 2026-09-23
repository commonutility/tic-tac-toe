"""Automated opponents for tic-tac-toe.

Every strategy implements the same interface: given the board and the mark
it is playing ("X" or "O"), return the index (0-8) of the square to play.

To add a new strategy (e.g. a learned model), subclass Opponent, implement
choose_move, and register it in OPPONENTS.
"""

import random

from tic_tac_toe import WIN_LINES, winner_of


class Opponent:
    def choose_move(self, board, mark):
        raise NotImplementedError


def empty_squares(board):
    return [i for i, value in enumerate(board) if not value]


def other(mark):
    return "O" if mark == "X" else "X"


class RandomOpponent(Opponent):
    """Plays a uniformly random legal move."""

    def choose_move(self, board, mark):
        return random.choice(empty_squares(board))


class HeuristicOpponent(Opponent):
    """Manually coded rules: win if possible, block if needed,
    otherwise prefer center, then corners, then edges."""

    PREFERRED_ORDER = [4, 0, 2, 6, 8, 1, 3, 5, 7]

    def choose_move(self, board, mark):
        for target in (mark, other(mark)):  # try to win first, then to block
            move = self._completing_move(board, target)
            if move is not None:
                return move
        for i in self.PREFERRED_ORDER:
            if not board[i]:
                return i

    @staticmethod
    def _completing_move(board, target):
        """Return the empty square that completes a line of two `target` marks."""
        for line in WIN_LINES:
            values = [board[i] for i in line]
            if values.count(target) == 2 and "" in values:
                return line[values.index("")]
        return None


class MinimaxOpponent(Opponent):
    """AI strategy: exhaustive minimax search. Plays perfectly (never loses)."""

    def __init__(self):
        self._cache = {}  # (board, to_play, me) -> (score, move); keeps the search fast

    def choose_move(self, board, mark):
        _, move = self._minimax(list(board), to_play=mark, me=mark)
        return move

    def _minimax(self, board, to_play, me):
        key = (tuple(board), to_play, me)
        if key in self._cache:
            return self._cache[key]
        result = self._search(board, to_play, me)
        self._cache[key] = result
        return result

    def _search(self, board, to_play, me):
        winner = winner_of(board)
        if winner == "Draw":
            return 0, None
        if winner is not None:
            return (1 if winner == me else -1), None

        best_score, best_move = None, None
        for i in empty_squares(board):
            board[i] = to_play
            score, _ = self._minimax(board, other(to_play), me)
            board[i] = ""
            maximizing = to_play == me
            if (
                best_score is None
                or (maximizing and score > best_score)
                or (not maximizing and score < best_score)
            ):
                best_score, best_move = score, i
        return best_score, best_move


OPPONENTS = {
    "random": RandomOpponent,
    "heuristic": HeuristicOpponent,
    "minimax": MinimaxOpponent,
}
