"""Automated opponents for tic-tac-toe.

Every strategy implements the same interface: given the board and the mark
it is playing ("X" or "O"), return the index (0-8) of the square to play.

To add a new strategy (e.g. a learned model), subclass Opponent, implement
choose_move, and register it in OPPONENTS.
"""

import json
import os
import random
import urllib.request

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


class AIOpponent(Opponent):
    """Basic AI strategy backed by the OpenAI API.

    Wiring is in place (API key from the OPENAI_API_KEY environment variable,
    endpoint constants, board formatting, legal-move list); the core logic --
    building the request and parsing the chosen move out of the reply -- is
    left to implement in choose_move.
    """

    URL = "https://api.openai.com/v1/chat/completions"
    MODEL = "gpt-4o-mini"

    def choose_move(self, board, mark):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set; export it before using the ai opponent"
            )

        legal = empty_squares(board)
        rows = [[board[r * 3 + c] or "." for c in range(3)] for r in range(3)]

        # TODO: build the request payload (self.MODEL, board `rows`, `mark`,
        # legal moves), POST it to self.URL with urllib as in JevOpponent,
        # parse the chosen square out of the reply, and return it.
        # Placeholder until then: plays the first empty square.
        return legal[0]


class JevOpponent(Opponent):
    """AI strategy backed by TypeSafe's Jev (System One) API.

    Asks Jev a single "choice" question whose options are exactly the legal
    squares, so the answer is always a valid move. Requires an API key from
    https://console.typesafe.ai in the TYPESAFE_API_KEY environment variable.
    """

    URL = "https://api.typesafe.ai/v1/systemone"
    MODEL = "jev-1.13.0"  # pinned: jev-latest can change answers when a new release ships

    def choose_move(self, board, mark):
        api_key = os.environ.get("TYPESAFE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "TYPESAFE_API_KEY is not set; get a key at https://console.typesafe.ai "
                "and run e.g.: export TYPESAFE_API_KEY=sk-..."
            )

        legal = empty_squares(board)
        rows = [[board[r * 3 + c] or "." for c in range(3)] for r in range(3)]
        payload = {
            "model": self.MODEL,
            "state": {
                "game": "tic-tac-toe",
                "board": rows,
                "notes": 'Rows are top to bottom, "." is an empty square. '
                "Squares are numbered 0-8, left to right, top to bottom.",
                "you_play": mark,
                "opponent_plays": other(mark),
            },
            "questions": {
                "move": {
                    "type": "choice",
                    "instructions": f"Pick the strongest tic-tac-toe move for {mark}: "
                    f"win now if possible, else block {other(mark)} from winning, "
                    "else take the square with the best position.",
                    "criteria": {
                        str(i): f"Play square {i} (row {i // 3}, column {i % 3})"
                        for i in legal
                    },
                }
            },
        }

        request = urllib.request.Request(
            self.URL,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            answer = json.loads(response.read())["answers"]["move"]
        return int(answer["choice"])


OPPONENTS = {
    "random": RandomOpponent,
    "heuristic": HeuristicOpponent,
    "minimax": MinimaxOpponent,
    "ai": AIOpponent,
    "jev": JevOpponent,
}
