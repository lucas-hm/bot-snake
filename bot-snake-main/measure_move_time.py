import asyncio
import os
import sys
import time

try:
    import websockets # type: ignore
except ImportError:
    websockets = None

# Configuración de paths
sys.path.insert(0, os.path.join(os.getcwd(), "bot-snake-main", "BOT", "dev_sentinel"))
sys.path.insert(0, os.path.join(os.getcwd(), "BOT", "dev_sentinel"))

from BOT.dev_sentinel.game_engine import GameMoveTool

# URL del servidor WebSocket para el test de Ping
WS_URL = "wss://codechallenge-server.up.railway.app/ws"


async def test_ping(num_samples=10):
    """Mide el tiempo de viaje de ida y vuelta (RTT/Ping) hacia el servidor WSS."""
    if websockets is None:
        print("\n⚠️ No se pudo ejecutar el test de Ping: falta instalar 'websockets'")
        return

    print(f"\n=== 1. TEST DE LATENCIA DE RED (PING / RTT) ===")
    print(f"Conectando a {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as ws:
            latencies = []
            print(f"Enviando {num_samples} pings de prueba...\n")

            for i in range(num_samples):
                start = time.perf_counter()

                # Frame Ping del protocolo WebSocket
                pong_waiter = await ws.ping()
                await pong_waiter  # Esperar respuesta Pong del servidor

                rtt_ms = (time.perf_counter() - start) * 1000
                latencies.append(rtt_ms)
                print(f" Muestra {i+1:2d}: {rtt_ms:.2f} ms")
                await asyncio.sleep(0.2)

            avg_ping = sum(latencies) / len(latencies)
            print("\n" + "=" * 40)
            print(f" Latencia mínima (Ping): {min(latencies):.2f} ms")
            print(f" Latencia promedio (RTT): {avg_ping:.2f} ms")
            print(f" Latencia máxima:        {max(latencies):.2f} ms")
            print("=" * 40)

    except Exception as e:
        print(f"❌ Error al conectar con el servidor WebSocket: {e}")


def measure_bot_performance(N=500):
    """Mide la velocidad de cálculo del algoritmo local del bot."""
    print(f"\n=== 2. BENCHMARK DE MOVIMIENTO LOCAL (N={N}) ===")

    board = {
        "my_body": [[5, 5], [4, 5], [3, 5]],
        "enemy_body": [[1, 1], [1, 2]],
        "foods": [[7, 7]],
        "width": 15,
        "height": 15,
    }
    payload = {
        "board": board,
        "rows": 15,
        "cols": 15,
        "side": "A",
        "turn_token": "t",
        "game_id": "g",
    }

    tool = GameMoveTool()

    # Warmup
    tool.execute(payload)

    times = []
    for _ in range(N):
        res = tool.execute(payload)
        ms = None
        if res and getattr(res, "metadata", None):
            ms = res.metadata.get("execution_time_ms")  # type: ignore
        if ms is None:
            # Fallback a medir localmente si metadata no está presente
            t0 = time.perf_counter()
            tool.execute(payload)
            ms = (time.perf_counter() - t0) * 1000
        times.append(ms)

    print(
        f"n={N}  min={min(times):.6f} ms  avg={sum(times)/len(times):.6f} ms  max={max(times):.6f} ms"
    )


async def main():
    # 1. Medir latencia de red WebSocket
    await test_ping(num_samples=10)

    # 2. Medir velocidad local del bot
    measure_bot_performance(N=500)


if __name__ == "__main__":
    asyncio.run(main())