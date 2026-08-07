import os
import sys
import json
import urllib.request

sys.path.insert(0, os.path.join(os.getcwd(), 'BOT', 'dev_sentinel'))
from game_engine import GameMoveTool

server_url = 'http://127.0.0.1:8000'
try:
    with urllib.request.urlopen(f'{server_url}/get_board') as r:
        data = json.loads(r.read().decode())
except Exception as e:
    print('GET error:', e)
    raise

board = data.get('board', {})
print('my_body:', board.get('my_body'))
print('foods (count):', len(board.get('foods', [])))
print('foods sample:', board.get('foods')[:10])

payload = {
    'board': board,
    'rows': board.get('height'),
    'cols': board.get('width'),
    'side': 'A',
    'turn_token': data.get('turn_token'),
    'game_id': data.get('game_id')
}

bot = GameMoveTool()
res = bot.execute(payload)
print('\nCommandResult.success:', res.success)
print('output:', res.output)
print('metadata:', res.metadata)

# Inspect internals
board_info = board
my_body = board_info.get('my_body', [])
foods = board_info.get('foods', [])
my_head = tuple(my_body[0]) if my_body else None

try:
    closest = bot._get_closest_food(my_head, foods, set(), board.get('width'), board.get('height'))
    print('closest_food (internal):', closest)
except Exception as e:
    print('closest_food error:', e)

try:
    mode = bot._get_strategy_mode(len(my_body), len(board_info.get('enemy_body', [])), len(foods), board.get('width'), board.get('height'))
    print('strategy_mode:', mode)
except Exception as e:
    print('strategy mode error:', e)

# Show BFS distance to closest food if available
try:
    if closest is not None:
        dist = bot._bfs_distance(my_head, tuple(closest), set(tuple(p) for p in my_body[:-1]) | set(tuple(p) for p in board_info.get('enemy_body', [])), board.get('width'), board.get('height'))
        print('bfs_distance to closest:', dist)
except Exception as e:
    print('bfs error:', e)
