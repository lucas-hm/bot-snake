import json
import time
import urllib.error
import urllib.request
from game_engine import GameMoveTool


def run_match_against_arena():
    bot = GameMoveTool()
    server_url = "http://localhost:8000"

    print("--- INICIANDO BATALLA: dev_sentinel vs MasterSnakeBot ---")

    # 1. Obtener el tablero inicial de la Arena
    try:
        req = urllib.request.Request(f"{server_url}/get_board")
        with urllib.request.urlopen(req) as response:
            game_data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Error conectando al servidor al inicio: {e}")
        return

    turn = 0
    while True:
        # 2. Calcular la jugada usando GameMoveTool
        try:
            command_result = bot.execute(game_data)
            direction = command_result.output.get("direction", "RIGHT")
        except Exception as e:
            print(f"Error en la lógica del bot (game_engine): {e}")
            break

        # 3. Construir el payload conservando todos los datos del estado + la dirección
        payload_data = dict(game_data)
        payload_data["direction"] = direction

        payload = json.dumps(payload_data).encode("utf-8")

        req_post = urllib.request.Request(
            f"{server_url}/send_move",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req_post) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            print(f"\n[ERROR 400] El servidor rechazó el payload: {error_body}")
            print(f"Payload enviado: {payload_data}\n")
            break
        except Exception as e:
            print(f"Error de red: {e}")
            break

        turn = result.get("turn", turn + 1)
        status = result.get("status")

        print(
            f"Turno {turn}: dev_sentinel envió -> {direction} | Estado: {status}"
        )

        # 4. Verificar fin de la partida
        if status == "finished":
            print("\n==========================================")
            print(f"PARTIDA FINALIZADA EN EL TURNO {turn}")
            print(f"GANADOR: {result.get('winner')}")
            print("==========================================\n")
            break

        # 5. Actualizar los datos para la siguiente iteración
        if "board" in result and isinstance(result["board"], (dict, str)):
            game_data["board"] = result["board"]
        if "turn_token" in result:
            game_data["turn_token"] = result["turn_token"]

        time.sleep(0.1)

if __name__ == "__main__":
    run_match_against_arena()