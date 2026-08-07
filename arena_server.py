from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random

WIDTH = 15
HEIGHT = 15

DIRECTIONS = {
    "UP": (0, -1),
    "DOWN": (0, 1),
    "LEFT": (-1, 0),
    "RIGHT": (1, 0),
}
REVERSE = {
    "UP": "DOWN",
    "DOWN": "UP",
    "LEFT": "RIGHT",
    "RIGHT": "LEFT",
}

# Estado global del juego en la Arena
GAME_STATE = {
    "game_id": "arena_match_001",
    "turn": 0,
    "status": "running",
    "winner": None,
    "board": {
        "width": WIDTH,
        "height": HEIGHT,
        "my_body": [[2, 2], [2, 1], [2, 0]],
        "enemy_body": [[12, 12], [12, 11], [12, 10]],
        "foods": [[7, 7], [3, 8], [10, 4]],
    },
    "my_direction": "RIGHT",
    "enemy_direction": "LEFT",
}


def in_bounds(pos):
    x, y = pos
    return 0 <= x < WIDTH and 0 <= y < HEIGHT


def snake_cells(body):
    return {tuple(pos) for pos in body}


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def closest_food(head, foods):
    if not foods:
        return None
    return min(foods, key=lambda food: manhattan(head, food))


def choose_enemy_direction(board):
    enemy_body = board["enemy_body"]
    my_body = board["my_body"]
    head = enemy_body[0]
    current = board["enemy_direction"]
    foods = board["foods"]

    blocked = snake_cells(enemy_body[:-1]) | snake_cells(my_body)
    valid_moves = []

    for direction, delta in DIRECTIONS.items():
        if direction == REVERSE.get(current):
            continue
        next_head = (head[0] + delta[0], head[1] + delta[1])
        if not in_bounds(next_head):
            continue
        if next_head in blocked:
            continue
        valid_moves.append((direction, next_head))

    if not valid_moves:
        for direction, delta in DIRECTIONS.items():
            next_head = (head[0] + delta[0], head[1] + delta[1])
            if in_bounds(next_head):
                valid_moves.append((direction, next_head))
        if not valid_moves:
            return current

    target_food = closest_food(head, foods)
    if target_food:
        best = min(valid_moves, key=lambda move: manhattan(move[1], target_food))
        return best[0]

    return random.choice(valid_moves)[0]


def move_snake(body, direction, grow):
    delta = DIRECTIONS.get(direction, DIRECTIONS["RIGHT"])
    head = body[0]
    next_head = [head[0] + delta[0], head[1] + delta[1]]
    new_body = [next_head] + body[:]
    if not grow:
        new_body.pop()
    return new_body


def is_collision(head, body, opponent_body, grow):
    if not in_bounds(tuple(head)):
        return True
    occupied = snake_cells(body[:-1] if not grow else body) | snake_cells(opponent_body)
    return tuple(head) in occupied


def resolve_head_on_head(my_head, enemy_head, my_body, enemy_body):
    if my_head != enemy_head:
        return False, False
    if len(my_body) > len(enemy_body):
        return False, True
    if len(enemy_body) > len(my_body):
        return True, False
    return True, True

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
        if self.path != "/send_move":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Ruta no encontrada"}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(post_data) if post_data else {}
        except Exception as e:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": f"JSON malformado: {e}"}).encode("utf-8"))
            return

        direction = payload.get("direction", "RIGHT") if isinstance(payload, dict) else "RIGHT"
        if direction not in DIRECTIONS:
            direction = GAME_STATE["my_direction"]
        if direction == REVERSE.get(GAME_STATE["my_direction"]):
            direction = GAME_STATE["my_direction"]

        GAME_STATE["my_direction"] = direction
        GAME_STATE["enemy_direction"] = choose_enemy_direction(GAME_STATE["board"])

        GAME_STATE["turn"] += 1
        current_turn = GAME_STATE["turn"]

        board = GAME_STATE["board"]
        foods = [tuple(pos) for pos in board["foods"]]

        my_next_head = [board["my_body"][0][0] + DIRECTIONS[direction][0], board["my_body"][0][1] + DIRECTIONS[direction][1]]
        enemy_next_head = [board["enemy_body"][0][0] + DIRECTIONS[GAME_STATE["enemy_direction"]][0], board["enemy_body"][0][1] + DIRECTIONS[GAME_STATE["enemy_direction"]][1]]

        my_grow = tuple(my_next_head) in foods
        if my_grow:
            foods.remove(tuple(my_next_head))

        enemy_grow = tuple(enemy_next_head) in foods
        if enemy_grow and tuple(enemy_next_head) in foods:
            foods.remove(tuple(enemy_next_head))

        board["my_body"] = move_snake(board["my_body"], direction, my_grow)
        board["enemy_body"] = move_snake(board["enemy_body"], GAME_STATE["enemy_direction"], enemy_grow)
        board["foods"] = [list(pos) for pos in foods]

        my_dead = is_collision(board["my_body"][0], board["my_body"], board["enemy_body"], my_grow)
        enemy_dead = is_collision(board["enemy_body"][0], board["enemy_body"], board["my_body"], enemy_grow)

        if tuple(board["my_body"][0]) == tuple(board["enemy_body"][0]):
            my_dead, enemy_dead = resolve_head_on_head(tuple(board["my_body"][0]), tuple(board["enemy_body"][0]), board["my_body"], board["enemy_body"])

        if my_dead and enemy_dead:
            GAME_STATE["status"] = "finished"
            GAME_STATE["winner"] = "tie"
        elif my_dead:
            GAME_STATE["status"] = "finished"
            GAME_STATE["winner"] = "MasterSnakeBot"
        elif enemy_dead:
            GAME_STATE["status"] = "finished"
            GAME_STATE["winner"] = "dev_sentinel"

        response = {
            "turn": current_turn,
            "status": GAME_STATE["status"],
            "winner": GAME_STATE["winner"],
            "board": GAME_STATE["board"],
            "turn_token": f"turn_{current_turn}",
        }

        self._set_headers(200)
        self.wfile.write(json.dumps(response).encode("utf-8"))


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
