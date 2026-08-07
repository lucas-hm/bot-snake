import os
import sys
import threading
import time

# Añadir ruta al directorio del bot para importar módulos locales
sys.path.insert(0, os.path.join(os.getcwd(), "BOT", "dev_sentinel"))

from arena_server import GAME_STATE, run
import client_runner

# Configurar 30 manzanas en el tablero local evitando cuerpos de serpiente
WIDTH = GAME_STATE["board"].get("width", 15)
occupied = set(tuple(p) for p in GAME_STATE["board"].get("my_body", [])) | set(tuple(p) for p in GAME_STATE["board"].get("enemy_body", []))
cells = [(x, y) for y in (5, 6) for x in range(WIDTH) if (x, y) not in occupied]
if len(cells) < 30:
	# si no hay suficientes en esas filas, añadir otras celdas vacías
	for y in range(GAME_STATE["board"].get("height", 15)):
		for x in range(WIDTH):
			if (x, y) not in occupied and (x, y) not in cells:
				cells.append((x, y))
foods = cells[:30]
GAME_STATE["board"]["foods"] = [list(pos) for pos in foods]

# Iniciar servidor local en segundo plano
server_thread = threading.Thread(target=run, kwargs={"port": 8000}, daemon=True)
server_thread.start()

# Dar tiempo para que el servidor inicie
time.sleep(1)

# Ejecutar la partida rápida
client_runner.run_match_against_arena()
