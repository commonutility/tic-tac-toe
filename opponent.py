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
from typing import Literal

from tic_tac_toe import WIN_LINES, winner_of

Mark = Literal["X", "O"]
Board = list[str]  # 9 cells, each "" | "X" | "O"
ScoreMove = tuple[int, int | None]  # (score for `me`, square to play or None if over)


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
        self._cache: dict[tuple[tuple[str, ...], Mark, Mark], ScoreMove] = {}

    def choose_move(self, board: Board, mark: Mark) -> int:
        # copy the board so search can write on it
        # ask _minimax for the (score, move) with to_play=mark and me=mark
        # return only the move
        raise NotImplementedError

    def _minimax(self, board: Board, to_play: Mark, me: Mark) -> ScoreMove:
        # if this (board, to_play, me) is already in the cache:
        #     return the cached tuple (score, move)
        # else:
        #     search through the scores for this position
        #     store the tuple in the cache
        #     return (score, move)
        raise NotImplementedError

    def _search(self, board: Board, to_play: Mark, me: Mark) -> ScoreMove:
        # if the game is a draw:
        #     return (0, None)
        # if someone has already won:
        #     return (1, None) if the winner is me, else (-1, None)
        # otherwise, for each empty square:
        #     play to_play there, recurse with the other player to move, then undo
        #     if it is my turn, keep the move with the highest score
        #     if it is their turn, keep the move with the lowest score
        # return (best_score, best_move)
        raise NotImplementedError


class AIOpponent(Opponent):
    """Basic AI strategy backed by the OpenAI API.

    Request wiring lives in _ask (API key, POST, parse a legal square).
    Implement choose_move by writing the decision instructions.
    """

    URL = "https://api.openai.com/v1/chat/completions"
    MODEL = "gpt-4o-mini"

    def choose_move(self, board, mark):
        legal = empty_squares(board)
        rows = [[board[r * 3 + c] or "." for c in range(3)] for r in range(3)]

        instructions = (
        f"Win immediately with {mark} if you can. "
        f"Otherwise block {other(mark)} from winning. "
        "Otherwise take the strongest remaining legal square."
        )
        return self._ask(rows, mark, legal, instructions)

    def _ask(self, rows, mark, legal, instructions):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set; export it before using the ai opponent"
            )

        payload = {
            "model": self.MODEL,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are playing tic-tac-toe. "
                        "Reply with only the integer index of the square you play."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"You play {mark}; opponent plays {other(mark)}.\n"
                        "Board (rows top to bottom, '.' is empty):\n"
                        + "\n".join(" ".join(row) for row in rows)
                        + "\nSquares are numbered 0-8, left to right, top to bottom.\n"
                        f"Legal moves: {legal}\n"
                        + instructions
                    ),
                },
            ],
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
            content = json.loads(response.read())["choices"][0]["message"]["content"]

        for token in "".join(ch if ch.isdigit() else " " for ch in content).split():
            move = int(token)
            if move in legal:
                return move
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
