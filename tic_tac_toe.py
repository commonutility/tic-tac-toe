"""Two-player Tic Tac Toe with a tkinter GUI.

Run with: python3 tic_tac_toe.py
Play against the computer with e.g.: python3 tic_tac_toe.py --opponent minimax
"""

import tkinter as tk

WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]


def winner_of(board):
    """Return "X", "O", "Draw", or None if the game is still in progress."""
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "Draw"
    return None


class Game:
    """Pure game state, independent of the UI."""

    def __init__(self):
        self.board = [""] * 9
        self.current_player = "X"
        self.winner = None  # "X", "O", "Draw", or None while in progress

    @property
    def over(self):
        return self.winner is not None

    def play(self, index):
        """Place the current player's mark at index. Returns True if the move was legal."""
        if self.over or self.board[index]:
            return False
        self.board[index] = self.current_player
        self._check_outcome()
        if not self.over:
            self.current_player = "O" if self.current_player == "X" else "X"
        return True

    def _check_outcome(self):
        self.winner = winner_of(self.board)


class TicTacToeApp:
    def __init__(self, root, opponent=None):
        self.root = root
        self.root.title("Tic Tac Toe")
        self.opponent = opponent  # plays O when set; None means two humans
        self.game = Game()

        self.status = tk.Label(root, font=("Helvetica", 16))
        self.status.grid(row=0, column=0, columnspan=3, pady=(10, 5))

        self.buttons = []
        for i in range(9):
            button = tk.Button(
                root,
                width=4,
                height=2,
                font=("Helvetica", 24, "bold"),
                command=lambda i=i: self.on_click(i),
            )
            button.grid(row=1 + i // 3, column=i % 3, padx=2, pady=2)
            self.buttons.append(button)

        tk.Button(root, text="New Game", command=self.reset).grid(
            row=4, column=0, columnspan=3, pady=(5, 10)
        )

        self.update_display()

    def on_click(self, index):
        if self.opponent and self.game.current_player == "O":
            return  # opponent's turn; ignore clicks
        if self.game.play(index):
            self.update_display()
            if self.opponent and not self.game.over:
                self.root.after(250, self.opponent_move)

    def opponent_move(self):
        if not self.game.over:
            self.game.play(self.opponent.choose_move(self.game.board, "O"))
            self.update_display()

    def reset(self):
        self.game = Game()
        self.update_display()

    def update_display(self):
        for button, mark in zip(self.buttons, self.game.board):
            button.config(text=mark)
        if self.game.winner == "Draw":
            self.status.config(text="It's a draw!")
        elif self.game.winner:
            self.status.config(text=f"{self.game.winner} wins!")
        else:
            self.status.config(text=f"{self.game.current_player}'s turn")


if __name__ == "__main__":
    import argparse

    from opponent import OPPONENTS

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--opponent",
        choices=sorted(OPPONENTS),
        help="have the computer play O with this strategy (default: two humans)",
    )
    args = parser.parse_args()
    opponent = OPPONENTS[args.opponent]() if args.opponent else None

    root = tk.Tk()
    TicTacToeApp(root, opponent=opponent)
    root.mainloop()
