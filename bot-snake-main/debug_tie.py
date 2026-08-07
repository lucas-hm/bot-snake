from arena_server import GAME_STATE, DIRECTIONS, is_collision, move_snake

board = GAME_STATE['board']
my_dir = GAME_STATE.get('my_direction', 'RIGHT')
enemy_dir = GAME_STATE.get('enemy_direction', 'LEFT')

print('Initial my_head:', board['my_body'][0])
print('Initial enemy_head:', board['enemy_body'][0])
print('My direction:', my_dir)
print('Enemy direction:', enemy_dir)

my_next = [board['my_body'][0][0] + DIRECTIONS[my_dir][0], board['my_body'][0][1] + DIRECTIONS[my_dir][1]]
enemy_next = [board['enemy_body'][0][0] + DIRECTIONS[enemy_dir][0], board['enemy_body'][0][1] + DIRECTIONS[enemy_dir][1]]

print('Computed my_next:', my_next)
print('Computed enemy_next:', enemy_next)

foods = [tuple(p) for p in board['foods']]
my_grow = tuple(my_next) in foods
enemy_grow = tuple(enemy_next) in foods

print('Foods:', foods)
print('my_grow:', my_grow, 'enemy_grow:', enemy_grow)

print('is_collision my_next:', is_collision(my_next, board['my_body'], board['enemy_body'], my_grow))
print('is_collision enemy_next:', is_collision(enemy_next, board['enemy_body'], board['my_body'], enemy_grow))

# simulate move
new_my_body = move_snake(board['my_body'], my_dir, my_grow)
new_enemy_body = move_snake(board['enemy_body'], enemy_dir, enemy_grow)
print('new_my_body:', new_my_body)
print('new_enemy_body:', new_enemy_body)

# check head-on-head
print('head_on_head:', tuple(new_my_body[0]) == tuple(new_enemy_body[0]))

# evaluate death flags using same logic as server
my_dead = is_collision(new_my_body[0], new_my_body, new_enemy_body, my_grow)
enemy_dead = is_collision(new_enemy_body[0], new_enemy_body, new_my_body, enemy_grow)
print('my_dead:', my_dead, 'enemy_dead:', enemy_dead)

# resolve head on head logic
if tuple(new_my_body[0]) == tuple(new_enemy_body[0]):
    print('Resolving head-on-head:')
    if len(new_my_body) > len(new_enemy_body):
        print('Enemy dies, my survives')
    elif len(new_enemy_body) > len(new_my_body):
        print('My dies, enemy survives')
    else:
        print('Both die (tie)')
