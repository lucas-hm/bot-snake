from collections import deque
from random import choice
import time
from interfaces import CommandResult, IBotCommand  # type: ignore

class GameMoveTool(IBotCommand):
    @property
    def name(self) -> str:
        return "calculate_move"

    def execute(self, data: dict, **kwargs) -> CommandResult:
        # CORRECCIÓN 1: Medir tiempo real (wall-clock time), no CPU time
        start_time = time.perf_counter()

        board_raw = data.get("board", {})
        game_id = data.get("game_id")
        turn_token = data.get("turn_token")
        side = data.get("side", "A")

        if isinstance(board_raw, str):
            board_info = self._parse_ascii_board(board_raw, side)
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
        my_tail = tuple(my_body_list[-1]) if len(my_body_list) > 0 else None
        enemy_head = (
            tuple(enemy_body_list[0]) if len(enemy_body_list) > 0 else None
        )

        can_eat_enemy = len(my_body_list) > len(enemy_body_list)

        my_obstacles = (
            set(tuple(p) for p in my_body_list[:-1])
            if len(my_body_list) > 1
            else set()
        )
        
        enemy_will_eat = enemy_head in food_positions if enemy_head else False
        if enemy_body_list and not enemy_will_eat:
            enemy_obstacles = set(tuple(p) for p in enemy_body_list[:-1])
        else:
            enemy_obstacles = set(tuple(p) for p in enemy_body_list) if enemy_body_list else set()

        obstacles = my_obstacles | enemy_obstacles

        enemy_danger_zones = set()
        if enemy_head and not can_eat_enemy:
            ex, ey = enemy_head
            for nx, ny in [
                (ex + 1, ey),
                (ex - 1, ey),
                (ex, ey + 1),
                (ex, ey - 1),
            ]:
                if 0 <= nx < grid_width and 0 <= ny < grid_height:
                    enemy_danger_zones.add((nx, ny))

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

        valid_moves = {}
        for move_name, target in directions.items():
            if move_name == forbidden_dir:
                continue
            if 0 <= target[0] < grid_width and 0 <= target[1] < grid_height:
                is_tail_move = my_tail is not None and target == my_tail
                if target not in obstacles and not (
                    is_tail_move and target in food_positions
                ):
                    valid_moves[move_name] = target

        if not valid_moves:
            for move_name, target in directions.items():
                if 0 <= target[0] < grid_width and 0 <= target[1] < grid_height:
                    is_tail_move = my_tail is not None and target == my_tail
                    if target not in obstacles and not (
                        is_tail_move and target in food_positions
                    ):
                        valid_moves[move_name] = target

        if not valid_moves:
            fallback = choice(["UP", "DOWN", "LEFT", "RIGHT"])
            return CommandResult(
                success=True,
                output={
                    "game_id": game_id,
                    "turn_token": turn_token,
                    "direction": fallback,
                    "row": 0,
                    "col": 0,
                },
                metadata={"strategy": "no_moves_left_emergency"},
            )

        safe_moves = {}
        for move_name, target in valid_moves.items():
            # CORRECCIÓN 2: Límite estricto de seguridad a 40ms en tiempo real
            if (time.perf_counter() - start_time) > 0.02:
                break

            if target in enemy_danger_zones and len(valid_moves) > 1:
                continue

            next_obstacles = set(obstacles)
            growing = target in food_positions
            if growing and my_tail is not None:
                next_obstacles.add(my_tail)

            available_space = self._flood_fill(
                target, next_obstacles, grid_width, grid_height
            )
            required_space = len(my_body_list) + (1 if growing else 0)
            if available_space >= required_space:
                safe_moves[move_name] = target

        candidates = safe_moves if safe_moves else valid_moves

        strategy_mode = self._get_strategy_mode(
            len(my_body_list),
            len(enemy_body_list),
            len(foods),
            grid_width,
            grid_height,
        )
        
        attack_target = (
            enemy_head if can_eat_enemy and enemy_head 
            else (tuple(enemy_body_list[-1]) if can_eat_enemy and enemy_body_list else None)
        )
        
        closest_food = None
        if foods and (time.perf_counter() - start_time) <= 0.04:
            closest_food = self._get_closest_food(my_head, foods, obstacles, grid_width, grid_height)

        trap_targets = set()
        trap_move = None
        if enemy_head and (time.perf_counter() - start_time) <= 0.04:
            ex, ey = enemy_head
            for nx, ny in [(ex + 1, ey), (ex - 1, ey), (ex, ey + 1), (ex, ey - 1)]:
                if 0 <= nx < grid_width and 0 <= ny < grid_height and (nx, ny) not in obstacles:
                    trap_targets.add((nx, ny))
            if len(trap_targets) <= 2:
                trap_move = self._find_intercept_move(
                    my_head, enemy_head, candidates, obstacles, grid_width, grid_height  # type: ignore
                )

        scored_moves = {}
        scored_move_details = {}
        best_move = None
        best_score = float("-inf")
        best_score_details = None

        # CORRECCIÓN 3: Evaluación de Voronoi una sola vez para no repetir Flood Fill en cada iteración
        enemy_space = None
        if enemy_head and (time.perf_counter() - start_time) <= 0.04:
            enemy_space = self._flood_fill(enemy_head, obstacles, grid_width, grid_height)

        for move_name, target in candidates.items():
            if (time.perf_counter() - start_time) > 0.04:
                break

            next_obstacles = set(obstacles)
            growing = target in food_positions
            if growing and my_tail is not None:
                next_obstacles.add(my_tail)

            space_after_move = self._flood_fill(
                target, next_obstacles, grid_width, grid_height
            )
            required_space = len(my_body_list) + (1 if growing else 0)
            if space_after_move < required_space:
                continue

            score, details = self._score_move(
                move_name=move_name,
                target=target,
                my_head=my_head,
                enemy_head=enemy_head,
                enemy_tail=tuple(enemy_body_list[-1]) if enemy_body_list else None,
                food_positions=food_positions,
                obstacles=next_obstacles,
                grid_width=grid_width,
                grid_height=grid_height,
                my_body_len=len(my_body_list),
                enemy_body_len=len(enemy_body_list),
                is_aggressive=can_eat_enemy,
                closest_food=closest_food,
                attack_target=attack_target,
                trap_targets=trap_targets,
                enemy_danger_zones=enemy_danger_zones,
                space_after_move=space_after_move,
                wall_distance=self._wall_distance(target, grid_width, grid_height),
                strategy_mode=strategy_mode,
                enemy_space=enemy_space,
            )
            scored_moves[move_name] = score
            scored_move_details[move_name] = details
            if score > best_score:
                best_score = score
                best_move = move_name
                best_score_details = details

        attack_move = None
        attack_score = float("-inf")
        if can_eat_enemy and attack_target and (time.perf_counter() - start_time) <= 0.04:
            attack_move = self._find_enemy_tail_move(
                my_head, attack_target, candidates, obstacles, grid_width, grid_height
            )
            if attack_move and attack_move in scored_moves:
                attack_score = scored_moves[attack_move] + 120.0

        trap_score = float("-inf")
        if trap_move and trap_move in scored_moves:
            trap_score = scored_moves[trap_move] + 40.0

        if attack_move and attack_score >= best_score + 10.0:
            attack_target_pos = candidates[attack_move]
            return CommandResult(
                success=True,
                output={
                    "game_id": game_id,
                    "turn_token": turn_token,
                    "direction": attack_move,
                    "row": attack_target_pos[0],
                    "col": attack_target_pos[1],
                },
                metadata={
                    "strategy": "Aggressive_Head_Hunter" if attack_target == enemy_head else "Attack_Enemy_Tail",
                    "chosen_move": attack_move,
                    "score_details": scored_move_details.get(attack_move),
                },
            )

        if trap_move and trap_score >= best_score + 10.0:
            trap_target_pos = candidates[trap_move]
            return CommandResult(
                success=True,
                output={
                    "game_id": game_id,
                    "turn_token": turn_token,
                    "direction": trap_move,
                    "row": trap_target_pos[0],
                    "col": trap_target_pos[1],
                },
                metadata={
                    "strategy": "Corner_Trap_Exploit",
                    "chosen_move": trap_move,
                    "score_details": scored_move_details.get(trap_move),
                },
            )

        if not best_move:
            best_move = choice(list(candidates.keys()))

        best_target_pos = candidates[best_move]
        return CommandResult(
            success=True,
            output={
                "game_id": game_id,
                "turn_token": turn_token,
                "direction": best_move,
                "row": best_target_pos[0],
                "col": best_target_pos[1],
            },
            metadata={
                "strategy": f"Scored_{strategy_mode}",
                "chosen_move": best_move,
                "score_details": best_score_details,
            },
        )

    def _get_strategy_mode(
        self,
        my_body_len: int,
        enemy_body_len: int,
        food_count: int,
        width: int,
        height: int,
    ) -> str:
        if my_body_len >= 8 or my_body_len >= enemy_body_len + 3:
            return "endgame"
        if my_body_len > enemy_body_len:
            return "aggressive"
        if food_count <= 2 or width * height <= 64:
            return "survival"
        return "balanced"

    def _score_move(
        self,
        move_name: str,
        target: tuple,
        my_head: tuple,
        enemy_head: tuple | None,
        enemy_tail: tuple | None,
        food_positions: set,
        obstacles: set,
        grid_width: int,
        grid_height: int,
        my_body_len: int,
        enemy_body_len: int,
        is_aggressive: bool,
        closest_food: tuple | None,
        attack_target: tuple | None,
        trap_targets: set,
        enemy_danger_zones: set | None = None,
        space_after_move: int | None = None,
        wall_distance: int | None = None,
        strategy_mode: str = "balanced",
        enemy_space: int | None = None,
    ) -> tuple[float, dict[str, float]]:
        if space_after_move is None:
            space_after_move = self._flood_fill(
                target, obstacles, grid_width, grid_height
            )

        if wall_distance is None:
            wall_distance = self._wall_distance(target, grid_width, grid_height)

        details = {
            "space_score": space_after_move * 0.15,
            "wall_score": wall_distance * 0.30,
            "food_score": 0.0,
            "direct_food_score": 0.0,
            "attack_score": 0.0,
            "trap_score": 0.0,
            "danger_head_penalty": 0.0,
            "danger_zone_penalty": 0.0,
            "strategy_bonus": 0.0,
            "safety_bonus": 0.0,
            "voronoi_asphyxia_bonus": 0.0,
        }

        score = details["space_score"] + details["wall_score"]

        if enemy_space is not None:
            if space_after_move > enemy_space * 1.4:
                details["voronoi_asphyxia_bonus"] = 75.0
                score += details["voronoi_asphyxia_bonus"]

        if closest_food is not None:
            food_distance = self._bfs_distance(
                target, closest_food, obstacles, grid_width, grid_height
            )
            if food_distance != float("inf"):
                food_weight = 3.0 if is_aggressive else 5.2
                details["food_score"] = max(0.0, 24.0 - food_distance) * food_weight
                score += details["food_score"]

        if target in food_positions:
            details["direct_food_score"] = 140.0
            score += details["direct_food_score"]

        if is_aggressive and attack_target is not None:
            details["attack_score"] = 120.0
            score += details["attack_score"]
            if target == attack_target:
                details["attack_score"] += 300.0
                score += 300.0
            else:
                attack_distance = self._bfs_distance(
                    target, attack_target, obstacles, grid_width, grid_height
                )
                if attack_distance != float("inf"):
                    bonus = max(0.0, 15.0 - attack_distance) * 60.0
                    details["attack_score"] += bonus
                    score += bonus

        if trap_targets and target in trap_targets:
            details["trap_score"] = 42.0
            score += details["trap_score"]

        if enemy_head is not None:
            danger_neighbors = {
                (enemy_head[0] + 1, enemy_head[1]),
                (enemy_head[0] - 1, enemy_head[1]),
                (enemy_head[0], enemy_head[1] + 1),
                (enemy_head[0], enemy_head[1] - 1),
            }
            if target in danger_neighbors or target == enemy_head:
                if is_aggressive:
                    details["danger_head_penalty"] = 80.0
                else:
                    details["danger_head_penalty"] = -22.0
                score += details["danger_head_penalty"]

        if enemy_danger_zones and target in enemy_danger_zones and not is_aggressive:
            details["danger_zone_penalty"] = -12.0
            score += details["danger_zone_penalty"]

        required_space = my_body_len + (1 if target in food_positions else 0)
        if space_after_move >= required_space + 2:
            details["safety_bonus"] = 10.0
            score += details["safety_bonus"]

        if strategy_mode == "aggressive":
            details["strategy_bonus"] = 60.0
            score += details["strategy_bonus"]
        elif strategy_mode == "survival":
            details["strategy_bonus"] = 30.0
            score += details["strategy_bonus"]
        elif strategy_mode == "endgame":
            details["strategy_bonus"] = 30.0
            score += details["strategy_bonus"]

        details["total"] = score
        return score, details

    def _parse_ascii_board(self, board_str: str, side: str) -> dict:
        lines = [line for line in board_str.split("\n") if line.strip()]

        my_head_char = "A" if side == "A" else "B"
        my_body_char = "a" if side == "A" else "b"
        enemy_head_char = "B" if side == "A" else "A"
        enemy_body_char = "b" if side == "A" else "a"

        my_head = None
        enemy_head = None
        raw_my_body = []
        raw_enemy_body = []
        foods = []

        height = len(lines)
        width = 0

        for y, line in enumerate(lines):
            row = line.strip("|")
            width = max(width, len(row))

            for x, char in enumerate(row):
                pos = (x, y)
                if char == my_head_char:
                    my_head = pos
                elif char == my_body_char:
                    raw_my_body.append(pos)
                elif char == enemy_head_char:
                    enemy_head = pos
                elif char == enemy_body_char:
                    raw_enemy_body.append(pos)
                elif char == "*":
                    foods.append(pos)

        full_my_body = self._reconstruct_body_chain(my_head, raw_my_body)  # type: ignore
        full_enemy_body = self._reconstruct_body_chain(
            enemy_head, raw_enemy_body  # type: ignore
        )

        return {
            "width": width,
            "height": height,
            "my_body": full_my_body,
            "enemy_body": full_enemy_body,
            "foods": foods,
        }

    def _reconstruct_body_chain(self, head: tuple, body_parts: list) -> list:
        if not head:
            return []
        chain = [head]
        unattached = list(body_parts)

        while unattached:
            curr = chain[-1]
            cx, cy = curr
            next_part = None

            for part in unattached:
                px, py = part
                if abs(px - cx) + abs(py - cy) == 1:
                    next_part = part
                    break

            if next_part:
                chain.append(next_part)
                unattached.remove(next_part)
            else:
                break

        return chain

    def _get_closest_food(
        self, start: tuple, foods: list, obstacles: set, width: int, height: int
    ) -> tuple:
        closest_food = None
        min_dist = float("inf")
        for food in foods:
            food_t = tuple(food)
            dist = self._bfs_distance(start, food_t, obstacles, width, height)
            if dist < min_dist:
                min_dist = dist
                closest_food = food_t
        return closest_food  # type: ignore

    def _find_intercept_move(
        self,
        my_head: tuple,
        enemy_head: tuple,
        candidates: dict,
        obstacles: set,
        width: int,
        height: int,
    ) -> str:
        if not enemy_head or enemy_head == (-1, -1):
            return None  # type: ignore

        exits_enemy = 0
        exits_coords = []
        ex, ey = enemy_head
        for nx, ny in [(ex + 1, ey), (ex - 1, ey), (ex, ey + 1), (ex, ey - 1)]:
            if (
                0 <= nx < width
                and 0 <= ny < height
                and (nx, ny) not in obstacles
            ):
                exits_enemy += 1
                exits_coords.append((nx, ny))

        if exits_enemy <= 2:
            for move_name, next_pos in candidates.items():
                if next_pos in exits_coords:
                    return move_name
        return None  # type: ignore

    def _flood_fill(
            self, start: tuple, obstacles: set, width: int, height: int
        ) -> int:
            if not isinstance(start, (tuple, list)) or len(start) < 2:
                return 0

            visited = set(obstacles)
            start_pos = (start[0], start[1])
            visited.add(start_pos)
            queue = deque([start_pos])
            space_count = 0

            while queue:
                curr = queue.popleft()
                if not isinstance(curr, (tuple, list)) or len(curr) < 2:
                    continue

                x, y = curr[0], curr[1]
                space_count += 1

                for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and (nx, ny) not in visited
                    ):
                        visited.add((nx, ny))
                        queue.append((nx, ny))

            return space_count

    def _wall_distance(self, position: tuple, width: int, height: int) -> int:
        x, y = position
        return min(x, y, width - 1 - x, height - 1 - y)

    def _find_enemy_tail_move(
        self,
        start: tuple,
        enemy_tail: tuple,
        candidates: dict,
        obstacles: set,
        width: int,
        height: int,
    ) -> str:
        shortest_dist = float("inf")
        best_attack_move = None

        for move_name, next_pos in candidates.items():
            dist = self._bfs_distance(
                next_pos, enemy_tail, obstacles, width, height
            )
            if dist < shortest_dist and dist != float("inf"):
                shortest_dist = dist
                best_attack_move = move_name

        return best_attack_move  # type: ignore

    def _bfs_best_move(
        self,
        start: tuple,
        target: tuple,
        candidates: dict,
        obstacles: set,
        width: int,
        height: int,
    ) -> str:
        shortest_dist = float("inf")
        best_direction = None

        for move_name, next_pos in candidates.items():
            dist = self._bfs_distance(
                next_pos, target, obstacles, width, height
            )
            if dist < shortest_dist:
                shortest_dist = dist
                best_direction = move_name

        return best_direction  # type: ignore

    def _bfs_distance(
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
                return dist

            x, y = curr
            for nx, ny in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))
        return float("inf")