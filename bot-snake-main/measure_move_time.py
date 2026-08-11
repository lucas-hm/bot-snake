# measure_move_time.py
import os, sys, time
sys.path.insert(0, os.path.join(os.getcwd(), 'bot-snake-main', 'BOT', 'dev_sentinel'))
from BOT.dev_sentinel.game_engine import GameMoveTool

# ejemplo mínimo de tablero
board = {
    "my_body": [[5,5],[4,5],[3,5]],
    "enemy_body": [[1,1],[1,2]],
    "foods": [[7,7]],
    "width": 15,
    "height": 15
}
payload = {"board": board, "rows": 15, "cols": 15, "side": "A", "turn_token": "t", "game_id": "g"}

tool = GameMoveTool()

# warmup
tool.execute(payload)

# medir N ejecuciones y recopilar los execution_time_ms devueltos
N = 500
times = []
for _ in range(N):
    res = tool.execute(payload)
    ms = None
    if res and getattr(res, "metadata", None):
        ms = res.metadata.get("execution_time_ms")
    if ms is None:
        # fallback a medir localmente si metadata no está presente
        t0 = time.perf_counter()
        tool.execute(payload)
        ms = (time.perf_counter() - t0) * 1000
    times.append(ms)

print(f"n={N}  min={min(times):.6f} ms  avg={sum(times)/len(times):.6f} ms  max={max(times):.6f} ms")