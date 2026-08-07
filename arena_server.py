from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Estado global del juego en la Arena
GAME_STATE = {
    "game_id": "arena_match_001",
    "turn": 0,
    "status": "running",
    "winner": None,
    "board": {
        "width": 15,
        "height": 15,
        "my_body": [[2, 2], [2, 1], [2, 0]],
        "enemy_body": [[12, 12], [12, 11], [12, 10]],
        "foods": [[7, 7], [3, 8], [10, 4]],
    },
}

class ArenaHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_GET(self):
        if self.path in ["/", "/get_board"]:
            self._set_headers(200)
            response = {
                "game_id": GAME_STATE["game_id"],
                "turn_token": f"turn_{GAME_STATE['turn']}",
                "side": "A",
                "board": GAME_STATE["board"],
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Ruta no encontrada"}).encode("utf-8"))

    def do_POST(self):
        if self.path == "/send_move":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode("utf-8")

            try:
                payload = json.loads(post_data) if post_data else {}
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": f"JSON malformado: {e}"}).encode("utf-8"))
                return

            # Extraer dirección enviada por el cliente
            direction = payload.get("direction", "RIGHT") if isinstance(payload, dict) else "RIGHT"

            # Avanzar turno
            GAME_STATE["turn"] += 1
            current_turn = GAME_STATE["turn"]

            # Mover la serpiente 'A' según la dirección
            head = list(GAME_STATE["board"]["my_body"][0])
            if direction == "UP":
                head[1] -= 1
            elif direction == "DOWN":
                head[1] += 1
            elif direction == "LEFT":
                head[0] -= 1
            elif direction == "RIGHT":
                head[0] += 1

            # Actualizar cuerpo
            GAME_STATE["board"]["my_body"].insert(0, head)
            GAME_STATE["board"]["my_body"].pop()

            # Verificar colisión con bordes
            x, y = head
            w, h = GAME_STATE["board"]["width"], GAME_STATE["board"]["height"]
            if x < 0 or x >= w or y < 0 or y >= h:
                GAME_STATE["status"] = "finished"
                GAME_STATE["winner"] = "MasterSnakeBot (por choque en pared)"

            # Responder al cliente
            response = {
                "turn": current_turn,
                "status": GAME_STATE["status"],
                "winner": GAME_STATE["winner"],
                "board": GAME_STATE["board"],
                "turn_token": f"turn_{current_turn}",
            }

            self._set_headers(200)
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Ruta no encontrada"}).encode("utf-8"))


def run(server_class=HTTPServer, handler_class=ArenaHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print("--------------------------------------------------")
    print(f"Servidor Arena listo en http://localhost:{port}")
    print("Escuchando peticiones GET y POST...")
    print("--------------------------------------------------")
    httpd.serve_forever()


if __name__ == "__main__":
    run()