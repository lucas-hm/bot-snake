import os
import sys
import threading
import time
import json
import urllib.request

sys.path.insert(0, os.path.join(os.getcwd(), "BOT", "dev_sentinel"))

from arena_server import GAME_STATE, run

# Configurar 30 manzanas en el tablero local
foods = [(x, 5) for x in range(15)] + [(x, 6) for x in range(15)]
GAME_STATE["board"]["foods"] = [list(pos) for pos in foods]

# Iniciar servidor local en segundo plano
server_thread = threading.Thread(target=run, kwargs={"port": 8000}, daemon=True)
server_thread.start()

time.sleep(1)

server_url = "http://localhost:8000"
max_turns = 500
turn = 0

print("--- INICIANDO PRUEBA LOCAL: dev_sentinel vs MasterSnakeBot ---")
print(f"Apples en tablero: {len(GAME_STATE['board']['foods'])}")

while turn < max_turns:
    try:
        req = urllib.request.Request(f"{server_url}/get_board")
        with urllib.request.urlopen(req) as response:
            game_data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error obteniendo tablero inicial: {e}")
        break

    direction = "RIGHT"
    payload = {"direction": direction}
    data = json.dumps(payload).encode("utf-8")
    req_post = urllib.request.Request(
        f"{server_url}/send_move",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req_post) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error enviando movimiento: {e}")
        break

    turn = result.get("turn", turn + 1)
    status = result.get("status", "unknown")
    winner = result.get("winner")

    print(f"Turno {turn}: status={status} winner={winner}")

    if status == "finished":
        print("\nPARTIDA FINALIZADA")
        print(f"Turnos jugados: {turn}")
        print(f"Ganador: {winner}")
        break

    time.sleep(0.05)
else:
    print("\nLímite de turnos alcanzado sin finalizar la partida.")
    print(f"Turnos jugados: {turn}")
    print(f"Estado actual: {GAME_STATE['status']}")
    print(f"Ganador actual: {GAME_STATE['winner']}")
