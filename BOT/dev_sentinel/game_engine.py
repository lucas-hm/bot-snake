from collections import deque
from random import randint
from interfaces import IBotCommand, CommandResult

class GameMoveTool(IBotCommand):
    @property
    def name(self) -> str:
        return "calculate_move"

    def execute(self, data: dict, **kwargs) -> CommandResult:
        """
        Calcula la jugada de alto rendimiento explotando:
        1. Liberación dinámica de colas (Tail Chasing).
        2. Táctica de acorralamiento e interceptación (Corner Trapping).
        3. Flood Fill para control de espacio seguro.
        4. BFS para camino mínimo a la comida.
        """
        board_data = data.get("board", {})
        game_id = data.get("game_id")
        turn_token = data.get("turn_token")

        # Fallback de seguridad si el tablero viene como String
        if isinstance(board_data, str):
            columns = board_data.find('|', 1) - 1 if '|' in board_data else 8
            selected_col = randint(0, max(0, columns))
            return CommandResult(
                success=True,
                output={"game_id": game_id, "turn_token": turn_token, "col": selected_col},
                metadata={"strategy": "fallback_string_board"}
            )

        # Parseo del estado del tablero
        grid_width = board_data.get("width", 10)
        grid_height = board_data.get("height", 10)
        my_head = tuple(board_data.get("my_head", (0, 0)))
        enemy_head = tuple(board_data.get("enemy_head", (-1, -1))) if "enemy_head" in board_data else None

        my_body_list = board_data.get("my_body", [])
        enemy_body_list = board_data.get("enemy_body", [])
        food = tuple(board_data.get("food", (0, 0)))

        # EXPLOTE 1: Descartar la cola final si se va a mover en este turno (Tail Chasing)
        my_obstacles = set(tuple(p) for p in my_body_list[:-1]) if len(my_body_list) > 1 else set()
        enemy_obstacles = set(tuple(p) for p in enemy_body_list[:-1]) if len(enemy_body_list) > 1 else set()
        obstacles = my_obstacles | enemy_obstacles

        # Direcciones de movimiento posibles
        directions = {
            "UP": (my_head[0], my_head[1] - 1),
            "DOWN": (my_head[0], my_head[1] + 1),
            "LEFT": (my_head[0] - 1, my_head[1]),
            "RIGHT": (my_head[0] + 1, my_head[1])
        }

        # Step 1: Filtrar movimientos válidos sin colisión
        valid_moves = {}
        for move_name, target in directions.items():
            if 0 <= target[0] < grid_width and 0 <= target[1] < grid_height:
                if target not in obstacles:
                    valid_moves[move_name] = target

        if not valid_moves:
            return CommandResult(
                success=True,
                output={"game_id": game_id, "turn_token": turn_token, "dir": "UP"},
                metadata={"strategy": "no_moves_left"}
            )

        # Step 2: Evaluar supervivencia con Flood Fill (Área disponible)
        safe_moves = {}
        for move_name, target in valid_moves.items():
            available_space = self._flood_fill(target, obstacles, grid_width, grid_height)
            if available_space >= len(my_body_list):
                safe_moves[move_name] = available_space

        candidates = safe_moves if safe_moves else valid_moves

        # EXPLOTE 2: Táctica de Acorralamiento (Interceptación)
        # Si el enemigo está cerca y podemos cortar su paso, priorizamos el corte
        trap_move = self._find_intercept_move(my_head, enemy_head, candidates, obstacles, grid_width, grid_height) # type: ignore
        if trap_move:
            return CommandResult(
                success=True,
                output={"game_id": game_id, "turn_token": turn_token, "dir": trap_move},
                metadata={"strategy": "Corner_Trap_Exploit", "chosen_move": trap_move}
            )

        # Step 3: BFS para camino óptimo hacia la comida
        best_move = self._bfs_best_move(my_head, food, candidates, obstacles, grid_width, grid_height)

        # Step 4: Modo supervivencia (mayor área libre disponible)
        if not best_move:
            best_move = max(
                candidates, 
                key=lambda m: self._flood_fill(candidates[m], obstacles, grid_width, grid_height)
            )

        move_payload = {
            "game_id": game_id,
            "turn_token": turn_token,
            "dir": best_move
        }

        return CommandResult(
            success=True,
            output=move_payload,
            metadata={"strategy": "SnakeMaster_UltraExploit", "chosen_move": best_move}
        )

    def _find_intercept_move(self, my_head: tuple, enemy_head: tuple, candidates: dict, obstacles: set, width: int, height: int) -> str:
        """Busca si hay una oportunidad de tapar la salida del rival antes de que escape."""
        if not enemy_head or enemy_head == (-1, -1):
            return None # type: ignore

        # Si el enemigo está pegado a los bordes del tablero
        exits_enemy = 0
        exits_coords = []
        ex, ey = enemy_head
        for nx, ny in [(ex+1, ey), (ex-1, ey), (ex, ey+1), (ex, ey-1)]:
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in obstacles:
                exits_enemy += 1
                exits_coords.append((nx, ny))

        # Si el rival tiene 1 o 2 salidas nomás, intentamos bloquear la coordenada de escape
        if exits_enemy <= 2:
            for move_name, next_pos in candidates.items():
                if next_pos in exits_coords:
                    return move_name
        return None # type: ignore

    def _flood_fill(self, start: tuple, obstacles: set, width: int, height: int) -> int:
        """Calcula casillas libres usando BFS corto."""
        visited = set(obstacles)
        visited.add(start)
        queue = deque([start])
        space_count = 0

        while queue:
            curr = queue.popleft()
            space_count += 1
            x, y = curr

            for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return space_count

    def _bfs_best_move(self, start: tuple, target: tuple, candidates: dict, obstacles: set, width: int, height: int) -> str:
        """Calcula qué movimiento inicial reduce más rápido la distancia al objetivo."""
        shortest_dist = float('inf')
        best_direction = None

        for move_name, next_pos in candidates.items():
            dist = self._bfs_distance(next_pos, target, obstacles, width, height)
            if dist < shortest_dist:
                shortest_dist = dist
                best_direction = move_name

        return best_direction # type: ignore

    def _bfs_distance(self, start: tuple, target: tuple, obstacles: set, width: int, height: int) -> float:
        queue = deque([(start, 0)])
        visited = set(obstacles)
        visited.add(start)

        while queue:
            curr, dist = queue.popleft()
            if curr == target:
                return dist

            x, y = curr
            for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))

        return float('inf')