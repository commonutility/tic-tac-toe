# Tic Tac Toe

A simple two-player tic-tac-toe game with optional computer opponents. Uses only the Python standard library — nothing to install.

## Play

**Desktop (tkinter):**

```bash
python3 tic_tac_toe.py                     # two humans
python3 tic_tac_toe.py --opponent minimax  # vs. the computer (random | heuristic | minimax)
```

**Browser:**

```bash
python3 web_tic_tac_toe.py   # then open http://localhost:8000
```

Use the "O is played by" dropdown to pick an opponent.

## Structure

- `tic_tac_toe.py` — game logic (`Game`, `winner_of`) and the tkinter UI
- `web_tic_tac_toe.py` — the same game served in the browser via a small JSON API
- `opponent.py` — automated opponents behind a common interface (`choose_move(board, mark) -> index`):
  - `random`: any legal move
  - `heuristic`: win / block / center / corners / edges
  - `minimax`: exhaustive search, never loses

To add a new strategy, subclass `Opponent` in `opponent.py` and register it in `OPPONENTS`.
