import os
import sys
import threading
import time
import json
import urllib.request

sys.path.insert(0, os.path.join(os.getcwd(), "BOT", "dev_sentinel"))

from arena_server import GAME_STATE, run
from game_engine import GameMoveTool

# Configurar 30 manzanas en el tablero local evitando cuerpos de serpiente
WIDTH = GAME_STATE["board"].get("width", 15)
occupied = set(tuple(p) for p in GAME_STATE["board"].get("my_body", [])) | set(tuple(p) for p in GAME_STATE["board"].get("enemy_body", []))
cells = [(x, y) for y in (5, 6) for x in range(WIDTH) if (x, y) not in occupied]
if len(cells) < 30:
    for y in range(GAME_STATE["board"].get("height", 15)):
        for x in range(WIDTH):
            if (x, y) not in occupied and (x, y) not in cells:
                cells.append((x, y))
foods = cells[:30]
GAME_STATE["board"]["foods"] = [list(pos) for pos in foods]

# Iniciar servidor local en segundo plano
server_thread = threading.Thread(target=run, kwargs={"port": 8000}, daemon=True)
server_thread.start()

time.sleep(1)

bot = GameMoveTool()
server_url = "http://localhost:8000"
max_turns = 500
turn = 0

print("--- INICIANDO PRUEBA FINAL LOCAL ---")
print(f"Manzanas en tablero: {len(GAME_STATE['board']['foods'])}")

try:
    req = urllib.request.Request(f"{server_url}/get_board")
    with urllib.request.urlopen(req, timeout=5) as response:
        game_data = json.loads(response.read().decode("utf-8"))
except Exception as e:
    print(f"Error obteniendo tablero inicial: {e}")
    raise

for _ in range(max_turns):
    command_result = bot.execute(game_data)
    direction = command_result.output.get("direction", "RIGHT") if isinstance(command_result.output, dict) else "RIGHT"

    payload_data = {"direction": direction}
    payload = json.dumps(payload_data).encode("utf-8")
    req_post = urllib.request.Request(
        f"{server_url}/send_move",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req_post, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error enviando movimiento: {e}")
        break

    turn = result.get("turn", turn + 1)
    status = result.get("status", "unknown")
    winner = result.get("winner")

    if status == "finished":
        print("\nPARTIDA FINALIZADA")
        print(f"Turnos jugados: {turn}")
        print(f"Ganador: {winner}")
        break

    game_data = {
        "board": result.get("board", {}),
        "game_id": result.get("game_id", GAME_STATE["game_id"]),
        "turn_token": result.get("turn_token", f"turn_{turn}"),
    }
    time.sleep(0.02)
else:
    print("\nLímite de turnos alcanzado sin finalizar la partida.")
    print(f"Turnos jugados: {turn}")
    print(f"Estado actual: {GAME_STATE['status']} | Ganador actual: {GAME_STATE['winner']}")
