"""Tic Tac Toe served in the browser at http://localhost:8000.

Reuses the Game class from tic_tac_toe.py; only the standard library is used.
Run with: python3 web_tic_tac_toe.py
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from opponent import OPPONENTS
from tic_tac_toe import Game

PORT = 8000

game = Game()
opponent_name = None  # None means two humans; otherwise a key in OPPONENTS

PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Tic Tac Toe</title>
<style>
  body { font-family: Helvetica, Arial, sans-serif; display: flex; flex-direction: column;
         align-items: center; margin-top: 40px; background: #f5f5f5; }
  h1 { margin-bottom: 8px; }
  #status { font-size: 20px; margin-bottom: 16px; min-height: 24px; }
  #board { display: grid; grid-template-columns: repeat(3, 90px); gap: 6px; }
  #board button { width: 90px; height: 90px; font-size: 42px; font-weight: bold;
                  border: none; border-radius: 8px; background: white; cursor: pointer;
                  box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
  #board button:hover:enabled { background: #eef; }
  #board button:disabled { color: #222; }
  #reset { margin-top: 20px; padding: 8px 24px; font-size: 16px; cursor: pointer; }
  #controls { margin-top: 16px; font-size: 15px; }
  #controls select { font-size: 15px; padding: 2px 6px; }
</style>
</head>
<body>
<h1>Tic Tac Toe</h1>
<div id="status"></div>
<div id="board"></div>
<div id="controls">
  O is played by:
  <select id="opponent">
    <option value="human">Human</option>
    <option value="random">Computer: random</option>
    <option value="heuristic">Computer: heuristic</option>
    <!-- <option value="minimax">Computer: minimax</option> -->
  </select>
</div>
<button id="reset">New Game</button>
<script>
const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");

const cells = [];
for (let i = 0; i < 9; i++) {
  const btn = document.createElement("button");
  btn.onclick = () => post("/move", { index: i });
  boardEl.appendChild(btn);
  cells.push(btn);
}
document.getElementById("reset").onclick = () => post("/reset", {});

const opponentEl = document.getElementById("opponent");
opponentEl.onchange = () => post("/opponent", { name: opponentEl.value });

function render(state) {
  state.board.forEach((mark, i) => {
    cells[i].textContent = mark;
    cells[i].disabled = Boolean(mark) || Boolean(state.winner);
  });
  opponentEl.value = state.opponent || "human";
  if (state.winner === "Draw") statusEl.textContent = "It's a draw!";
  else if (state.winner) statusEl.textContent = state.winner + " wins!";
  else statusEl.textContent = state.current_player + "'s turn";
}

async function post(url, body) {
  const res = await fetch(url, { method: "POST", body: JSON.stringify(body) });
  render(await res.json());
}

fetch("/state").then(res => res.json()).then(render);
</script>
</body>
</html>
"""


def state():
    return {
        "board": game.board,
        "current_player": game.current_player,
        "winner": game.winner,
        "opponent": opponent_name,
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, content_type):
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_state(self):
        self._send(json.dumps(state()), "application/json")

    def do_GET(self):
        if self.path == "/":
            self._send(PAGE, "text/html")
        elif self.path == "/state":
            self._send_state()
        else:
            self.send_error(404)

    def do_POST(self):
        global game, opponent_name
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or "{}")
        if self.path == "/move":
            if game.play(body["index"]) and opponent_name and not game.over:
                opponent = OPPONENTS[opponent_name]()
                game.play(opponent.choose_move(game.board, game.current_player))
            self._send_state()
        elif self.path == "/opponent":
            name = body.get("name")
            opponent_name = name if name in OPPONENTS else None
            self._send_state()
        elif self.path == "/reset":
            game = Game()
            self._send_state()
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    print(f"Serving Tic Tac Toe at http://localhost:{PORT}")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
