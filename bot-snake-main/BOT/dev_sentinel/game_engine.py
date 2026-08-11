from collections import deque
from random import choice
import time
from interfaces import CommandResult, IBotCommand  # type: ignore

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
            board_info = self._parse_ascii_board(board_raw, side) # type: ignore
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
                output={"game_id": game_id, "turn_token": turn_token, "direction": "RIGHT", "row": 0, "col": 0},
                metadata={"strategy": "no_body_found"},
            )

        my_head = tuple(my_body_list[0])
        my_tail = tuple(my_body_list[-1]) if len(my_body_list) > 0 else None
        enemy_head = tuple(enemy_body_list[0]) if len(enemy_body_list) > 0 else None

        can_eat_enemy = len(my_body_list) > len(enemy_body_list)
        my_obstacles = set(tuple(p) for p in my_body_list[:-1]) if len(my_body_list) > 1 else set()
        
        enemy_will_eat = enemy_head in food_positions if enemy_head else False
        if enemy_body_list and not enemy_will_eat:
            enemy_obstacles = set(tuple(p) for p in enemy_body_list[:-1])
        else:
            enemy_obstacles = set(tuple(p) for p in enemy_body_list) if enemy_body_list else set()

        obstacles = my_obstacles | enemy_obstacles

        # Determinar dirección prohibida (cuello)
        forbidden_dir = None
        if len(my_body_list) >= 2:
            hx, hy = my_body_list[0]
            nx, ny = my_body_list[1]
            if hx > nx: forbidden_dir = "LEFT"
            elif hx < nx: forbidden_dir = "RIGHT"
            elif hy > ny: forbidden_dir = "UP"
            elif hy < ny: forbidden_dir = "DOWN"

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
                is_tail_move = my_tail is not None and target == my_tail
                if target not in obstacles and not (is_tail_move and target in food_positions):
                    valid_moves[move_name] = target

        if not valid_moves:
            fallback = choice(["UP", "DOWN", "LEFT", "RIGHT"])
            elapsed = (time.perf_counter() - start_time) * 1000
            return CommandResult(
                success=True,
                output={"game_id": game_id, "turn_token": turn_token, "direction": fallback, "row": 0, "col": 0},
                metadata={"strategy": "emergency_no_moves", "execution_time_ms": elapsed},
            )

        dist_map = self._get_bfs_distance_map(my_head, obstacles, grid_width, grid_height)
        dist_map = {}

        closest_food = None
        min_food_dist = float("inf")
        for f in food_positions:
            # Reemplazado BFS por Distancia Manhattan instantánea O(1)
            d = abs(f[0] - my_head[0]) + abs(f[1] - my_head[1])
            if d < min_food_dist:
                min_food_dist = d
                closest_food = f

        scored_moves = {}
        best_move = None
        best_score = float("-inf")

        required_space = len(my_body_list)

        for move_name, target in valid_moves.items():
            space_after = self._flood_fill(target, obstacles, grid_width, grid_height)
            if space_after < required_space and len(valid_moves) > 1:
                continue
            space_after = 0

            # Scoring simplificado y directo
            score = 0.0
            
            if target in food_positions:
                score += 100.0
            elif closest_food:
                # Reemplazado BFS por Distancia Manhattan
                food_dist_from_target = abs(closest_food[0] - target[0]) + abs(closest_food[1] - target[1])
                score += max(0.0, 30.0 - food_dist_from_target) * 3.0

            scored_moves[move_name] = score
            if score > best_score:
                best_score = score
                best_move = move_name

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
                "strategy": "No_BFS_No_FloodFill_Test",
                "chosen_move": best_move,
                "execution_time_ms": round(elapsed_ms, 4),
            },
        )

    def _get_bfs_distance_map(self, start: tuple, obstacles: set, width: int, height: int) -> dict:
        queue = deque([(start, 0)])
        visited = {start: 0}
        while queue:
            curr, dist = queue.popleft()
            x, y = curr
            for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in obstacles:
                    if (nx, ny) not in visited:
                        visited[(nx, ny)] = dist + 1
                        queue.append(((nx, ny), dist + 1))
        return visited

    def _bfs_distance_fast(self, start: tuple, target: tuple, obstacles: set, width: int, height: int) -> float:
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
        return float("inf")

    def _flood_fill(self, start: tuple, obstacles: set, width: int, height: int) -> int:
        visited = set(obstacles)
        visited.add(start)
        queue = deque([start])
        space_count = 0
        while queue:
            x, y = queue.popleft()
            space_count += 1
            for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return space_count