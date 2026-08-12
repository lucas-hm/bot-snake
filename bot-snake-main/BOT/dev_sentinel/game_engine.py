from collections import deque
from random import choice
import time

from .interfaces import CommandResult, IBotCommand  # type: ignore

class GameMoveTool(IBotCommand):
    @property
    def name(self) -> str:
        return "calculate_move"

    def execute(self, data: dict, **kwargs) -> CommandResult:
        start_time = time.perf_counter()

        board_raw = data.get("board", {})
        game_id = data.get("game_id")
        turn_token = data.get("turn_token")
        side = data.get("side", "A")

        if isinstance(board_raw, str):
            board_info = self._parse_ascii_board(board_raw, side)  # type: ignore
        else:
            board_info = board_raw

        cols = data.get("cols")
        rows = data.get("rows")
        grid_width = cols if cols is not None else board_info.get("width", 15)
        grid_height = rows if rows is not None else board_info.get("height", 15)

        my_body_list = board_info.get("my_body", [])
        enemy_body_list = board_info.get("enemy_body", [])
        foods = board_info.get("foods", [])
        food_positions = set(tuple(p) for p in foods)

        if not my_body_list:
            return CommandResult(
                success=True,
                output={
                    "game_id": game_id,
                    "turn_token": turn_token,
                    "direction": "RIGHT",
                    "row": 0,
                    "col": 0,
                },
                metadata={"strategy": "no_body_found"},
            )

        my_head = tuple(my_body_list[0])
        my_tail = tuple(my_body_list[-1]) if my_body_list else None
        enemy_head = tuple(enemy_body_list[0]) if enemy_body_list else None

        my_obstacles = (
            set(tuple(p) for p in my_body_list[:-1])
            if len(my_body_list) > 1
            else set()
        )

        enemy_will_eat = (
            enemy_head in food_positions if enemy_head else False
        )

        if enemy_body_list and not enemy_will_eat:
            enemy_obstacles = set(
                tuple(p) for p in enemy_body_list[:-1]
            )
        else:
            enemy_obstacles = (
                set(tuple(p) for p in enemy_body_list)
                if enemy_body_list
                else set()
            )

        obstacles = my_obstacles | enemy_obstacles

        # Determinar dirección prohibida (cuello)
        forbidden_dir = None

        if len(my_body_list) >= 2:
            hx, hy = my_body_list[0]
            nx, ny = my_body_list[1]

            if hx > nx:
                forbidden_dir = "LEFT"
            elif hx < nx:
                forbidden_dir = "RIGHT"
            elif hy > ny:
                forbidden_dir = "UP"
            elif hy < ny:
                forbidden_dir = "DOWN"

        directions = {
            "UP": (my_head[0], my_head[1] - 1),
            "DOWN": (my_head[0], my_head[1] + 1),
            "LEFT": (my_head[0] - 1, my_head[1]),
            "RIGHT": (my_head[0] + 1, my_head[1]),
        }

        # Filtrar movimientos válidos inmediatos
        valid_moves = {}

        for move_name, target in directions.items():
            if move_name == forbidden_dir:
                continue

            if 0 <= target[0] < grid_width and 0 <= target[1] < grid_height:
                is_tail_move = (
                    my_tail is not None and target == my_tail
                )

                if target not in obstacles and not (
                    is_tail_move and target in food_positions
                ):
                    valid_moves[move_name] = target

        if not valid_moves:
            fallback = choice(["UP", "DOWN", "LEFT", "RIGHT"])
            elapsed = (time.perf_counter() - start_time) * 1000

            return CommandResult(
                success=True,
                output={
                    "game_id": game_id,
                    "turn_token": turn_token,
                    "direction": fallback,
                    "row": 0,
                    "col": 0,
                },
                metadata={
                    "strategy": "emergency_no_moves",
                    "execution_time_ms": elapsed,
                },
            )

        # ============================================================
        # BFS desde la cabeza para encontrar la comida más cercana
        # ============================================================

        dist_map = self._get_bfs_distance_map(
            my_head,
            obstacles,
            grid_width,
            grid_height,
        )

        closest_food = None
        min_food_dist = float("inf")

        for food in food_positions:
            distance = dist_map.get(
                food,
                abs(food[0] - my_head[0])
                + abs(food[1] - my_head[1]),
            )

            if distance < min_food_dist:
                min_food_dist = distance
                closest_food = food

        # ============================================================
        # Preparar posiciones peligrosas de la cabeza enemiga
        # ============================================================

        enemy_head_neighbors = set()

        if enemy_head:
            enemy_head_neighbors = {
                (enemy_head[0] + 1, enemy_head[1]),
                (enemy_head[0] - 1, enemy_head[1]),
                (enemy_head[0], enemy_head[1] + 1),
                (enemy_head[0], enemy_head[1] - 1),
            }

        # ============================================================
        # Evaluación de movimientos
        # ============================================================

        scored_moves = {}
        best_move = None
        best_score = float("-inf")
        required_space = len(my_body_list)

        for move_name, target in valid_moves.items():

            # --------------------------------------------------------
            # 1. PELIGRO CABEZA-CABEZA
            #
            # Si nuestra serpiente no es más larga que la enemiga,
            # evitamos entrar en una casilla adyacente a su cabeza.
            # --------------------------------------------------------

            if (
                enemy_head
                and target in enemy_head_neighbors
                and len(my_body_list) <= len(enemy_body_list)
            ):
                continue

            # --------------------------------------------------------
            # 2. FLOOD FILL
            #
            # Solo ejecutamos Flood Fill después de descartar
            # movimientos obviamente peligrosos.
            # --------------------------------------------------------

            space_after = self._flood_fill(
                target,
                obstacles,
                grid_width,
                grid_height,
            )

            if space_after < required_space and len(valid_moves) > 1:
                continue

            score = 0.0

            # --------------------------------------------------------
            # 3. COMIDA
            # --------------------------------------------------------

            if target in food_positions:
                score += 100.0

            elif closest_food:
                food_dist_from_target = self._bfs_distance_fast(
                    target,
                    closest_food,
                    obstacles,
                    grid_width,
                    grid_height,
                )

                if food_dist_from_target == float("inf"):
                    food_dist_from_target = (
                        abs(closest_food[0] - target[0])
                        + abs(closest_food[1] - target[1])
                    )

                score += (
                    max(0.0, 30.0 - food_dist_from_target) * 3.0
                )

            # --------------------------------------------------------
            # 4. PERSECUCIÓN DE COLA
            #
            # Si no hay comida disponible, favorecemos movimientos
            # que acerquen nuestra cabeza a nuestra cola.
            # --------------------------------------------------------

            elif my_tail is not None:
                tail_dist = self._bfs_distance_fast(
                    target,
                    my_tail,
                    obstacles,
                    grid_width,
                    grid_height,
                )

                if tail_dist == float("inf"):
                    tail_dist = (
                        abs(my_tail[0] - target[0])
                        + abs(my_tail[1] - target[1])
                    )

                score += max(0.0, 20.0 - tail_dist) * 2.0

            # --------------------------------------------------------
            # 5. CASTIGO POR PAREDES
            #
            # Penalizamos posiciones en los bordes para mantener
            # mayor libertad de movimiento.
            # --------------------------------------------------------

            if (
                target[0] == 0
                or target[0] == grid_width - 1
                or target[1] == 0
                or target[1] == grid_height - 1
            ):
                score -= 10.0

            scored_moves[move_name] = score

            if score > best_score:
                best_score = score
                best_move = move_name

        # ============================================================
        # Si todas las jugadas fueron descartadas por heurísticas
        # de seguridad, elegimos una de las jugadas válidas originales.
        # ============================================================

        if not best_move:
            best_move = choice(list(valid_moves.keys()))

        best_target = valid_moves[best_move]

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return CommandResult(
            success=True,
            output={
                "game_id": game_id,
                "turn_token": turn_token,
                "direction": best_move,
                "row": best_target[0],
                "col": best_target[1],
            },
            metadata={
                "strategy": "BFS_Active_Strategy",
                "chosen_move": best_move,
                "execution_time_ms": round(elapsed_ms, 4),
            },
        )

    def _get_bfs_distance_map(
        self,
        start: tuple,
        obstacles: set,
        width: int,
        height: int,
    ) -> dict:
        queue = deque([(start, 0)])
        visited = {start: 0}

        while queue:
            curr, dist = queue.popleft()
            x, y = curr

            for nx, ny in [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
            ]:
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and (nx, ny) not in obstacles
                ):
                    if (nx, ny) not in visited:
                        visited[(nx, ny)] = dist + 1
                        queue.append(((nx, ny), dist + 1))

        return visited

    def _bfs_distance_fast(
        self,
        start: tuple,
        target: tuple,
        obstacles: set,
        width: int,
        height: int,
    ) -> float:
        queue = deque([(start, 0)])
        visited = set(obstacles)
        visited.add(start)

        while queue:
            curr, dist = queue.popleft()

            if curr == target:
                return float(dist)

            x, y = curr

            for nx, ny in [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
            ]:
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))

        return float("inf")

    def _flood_fill(
        self,
        start: tuple,
        obstacles: set,
        width: int,
        height: int,
    ) -> int:
        visited = set(obstacles)
        visited.add(start)

        queue = deque([start])
        space_count = 0

        while queue:
            x, y = queue.popleft()
            space_count += 1

            for nx, ny in [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1),
            ]:
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return space_count