# 🐍 Arquitectura del Bot Depredador - Dev Sentinel

## Estructura General: "Alien Isolation Snake Edition"

Tu bot es como el **Xenomorfo de Alien Isolation** porque:
1. **Persigue de manera inteligente** cuando ve presa (enemigo pequeño)
2. **Evita peligro letal** (paredes, cuerpo propio, enemigos grandes)
3. **Adapta su estrategia** según si es predador o presa
4. **Usa el espacio** para acorralar a enemigos débiles
5. **Tiene sentido de supervivencia** con respaldos (wall-hugging)

---

## 🔍 SISTEMA DE PERCEPCIÓN

### `_parse_ascii_board(board_str, side)` - EL OJO DEL DEPREDADOR
**¿Qué hace?**
Convierte el tablero ASCII del servidor en datos estructurados que el bot pueda entender.

**Ejemplo:**
```
|       |
|  aaA *|    <- Tu serpiente (A = cabeza, a = cuerpo)
|    B  |    <- Enemigo (B = cabeza)
|  Bbb  |    <- Cuerpo del enemigo
|   *   |    <- Comida (*)
```

**Se convierte en:**
```python
{
    "my_body": [(5,1), (2,1), (2,2), (2,3)],    # Cabeza primero → cola al final
    "enemy_body": [(4,2), (2,3), (2,4), (2,5)], # Igual: cabeza → cola
    "foods": [(6,1), (3,4)],                     # Ubicaciones de comida
    "width": 7, "height": 5
}
```

**¿Por qué es peligroso?**
- Reconstruye la cadena completa del cuerpo (cabeza→cuello→cola) usando `_reconstruct_body_chain()`
- Sin esto, no sabrías dónde está realmente el enemigo
- El enemigo puede "ocultar" su estructura si no lo parseas bien

---

## ⚡ SISTEMA DE ANÁLISIS DEFENSIVO

### 1. `execute()` - EL CEREBRO PRINCIPAL
**¿Qué hace?**
Es el orquestador maestro. Decide en qué orden intentar estrategias:

**Orden de decisión (como un depredador astuto):**
```
if NO_BODY:
    return SAFE_DEFAULT (RIGHT)

STEP 1: ANALIZAR PELIGROS
├─ Construir obstáculos (tu cuerpo + cuerpo enemigo)
├─ Definir zonas peligrosas (alrededor de la cabeza enemiga)
└─ Bloquear giros de 180°

STEP 2: GENERAR MOVIMIENTOS VÁLIDOS
├─ Filtrar movimientos que no choquen con paredes
├─ Filtrar movimientos que no choquen contigo mismo
└─ Evitar la cola si hay comida (te atascarías)

STEP 3: EVALUAR SEGURIDAD (Flood Fill)
├─ Calcular espacio libre después de cada movimiento
└─ Solo permitir movimientos con espacio >= tamaño de tu cuerpo

STEP 4: OFENSIVA (SI ERES MÁS GRANDE)
├─ Detectar si `len(my_body) > len(enemy_body)`
├─ Perseguir la cola del enemigo
└─ RETORNAR ATAQUE (máxima prioridad)

STEP 5: TRAMPA
├─ Intentar acorralar al enemigo
├─ Si está acorralado, cortarle el escape
└─ RETORNAR TRAMPA

STEP 6: ALIMENTO
├─ Si hay comida, buscar la más cercana con BFS
├─ Validar que hay espacio después de comer
└─ RETORNAR COMIDA

STEP 7: SUPERVIVENCIA (Wall-Hugging)
├─ Elegir el movimiento con más espacio libre
├─ Priorizar mantenerse cerca de la pared
└─ RETORNAR SEGURO
```

**¿Por qué es depredador?**
- La lógica ofensiva viene ANTES que la de comida
- Si eres más grande, **atacas primero, comes después**
- Esto hace que sea agresivo y oportunista

---

## 🎯 SISTEMA DEFENSIVO PURO

### 2. `obstacles` y `enemy_danger_zones` - EL MAPA DE MINAS
```python
my_obstacles = {todas tus vértebras excepto la cola}
enemy_obstacles = {todas las vértebras del enemigo excepto su cola}
obstacles = my_obstacles | enemy_obstacles

enemy_danger_zones = {celdas adyacentes a la cabeza enemiga}
```

**¿Por qué?**
- La cola NO es obstáculo porque se mueve (liberación dinámica)
- Si el enemigo es tu tamaño o mayor, evitas 4 celdas alrededor de su cabeza
- Si es más pequeño, puedes atacar esas zonas

**Analogía:** Como el Xenomorfo que sabe dónde NO debe entrar para no ser visto.

---

### 3. `forbidden_dir` - EL BLOQUEO DE GIRO MORTAL
```python
if head_x > prev_segment_x:
    forbidden_dir = "LEFT"  # No puedes girar 180° hacia atrás
elif head_x < prev_segment_x:
    forbidden_dir = "RIGHT"
elif head_y > prev_segment_y:
    forbidden_dir = "UP"
elif head_y < prev_segment_y:
    forbidden_dir = "DOWN"
```

**¿Por qué es crítico?**
- Si te estás moviendo DERECHA, no puedes girar IZQUIERDA instantáneamente
- Esto mata al bot garantizado
- Es la regla más importante de Snake

---

### 4. `valid_moves` y `safe_moves` - EL FILTRADO MÚLTIPLE
```python
# STEP 1: Movimientos físicamente válidos
valid_moves = {
    "UP": (x, y-1),
    "DOWN": (x, y+1),
    "LEFT": (x-1, y),
    "RIGHT": (x+1, y),
}
# Filtrados si:
# - Están dentro del tablero
# - No colisionan con obstáculos
# - No intentan girar 180°

# STEP 2: Movimientos seguros (con espacio)
safe_moves = {
    move: target for move in valid_moves
    if flood_fill(target) >= len(body)
}
```

**¿Por qué dos filtros?**
- `valid_moves`: responde "¿puedo físicamente moverme ahí?"
- `safe_moves`: responde "¿tendré espacio para no quedar atrapado?"

**Analogía:** El Xenomorfo no solo entra por un agujero (válido), también verifica que tendrá escape (seguro).

---

## 🔨 SISTEMA OFENSIVO: LA CAZA

### 5. `_find_enemy_tail_move()` - EL ATAQUE COORDINADO
```python
def _find_enemy_tail_move(start, enemy_tail, candidates, obstacles, width, height):
    """Busca el camino más corto a la cola del enemigo"""
    for move in candidates:
        dist = BFS_distance(move, enemy_tail, obstacles, width, height)
    return move_with_shortest_distance
```

**¿Cómo funciona?**
1. Itera sobre cada movimiento posible (`candidates`)
2. Calcula BFS desde esa posición hasta la cola del enemigo
3. Retorna el movimiento que acorta más la distancia

**Analogía depredador:**
- El Xenomorfo no solo ve a su presa, la persigue tomando el camino más corto
- Ignora distracciones (comida) si hay presa cerca
- Es obsesivo: una vez que decide atacar, va a por ti

---

### 6. `_find_intercept_move()` - EL ACORRALAMIENTO
```python
def _find_intercept_move(my_head, enemy_head, candidates, obstacles, width, height):
    """Si el enemigo está acorralado (2+ salidas), intenta bloquearlo"""
    exits = count(libre_adyacente_a_enemy_head)
    if exits <= 2:
        for move in candidates:
            if move_reaches_enemy_exit:
                return move  # Bloquea escape
```

**¿Por qué es mortal?**
- Detecta cuántas salidas tiene el enemigo
- Si está acorralado en una esquina/túnel, corta el escape
- Es como el Xenomorfo que sabe que su presa no tiene salida

---

## 🧭 SISTEMA DE NAVEGACIÓN: BÚSQUEDA INTELIGENTE

### 7. `_bfs_distance()` y `_bfs_best_move()` - EL GPS DEL DEPREDADOR
```python
def _bfs_distance(start, target, obstacles, width, height):
    """Busca el camino más corto usando BFS (Breadth-First Search)"""
    queue = [(start, 0)]
    visited = set()
    
    while queue:
        current, dist = queue.popleft()
        if current == target:
            return dist  # ENCONTRADO
        
        for neighbor in (current + UP, current + DOWN, current + LEFT, current + RIGHT):
            if neighbor not in obstacles and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + 1))
    
    return infinity  # No hay camino
```

**Pasos:**
1. BFS explora todas las celdas accesibles en círculos concéntricos
2. Cuando llega al objetivo, devuelve el número de pasos
3. Garantiza encontrar el camino MÁS CORTO

**Analogía:**
- El Xenomorfo no prueba caminos al azar
- Usa el camino más óptimo, como si tuviera un mapa mental del escenario
- Si hay múltiples rutas, elige la más corta

---

### 8. `_flood_fill()` - EL DETECTOR DE TRAMPAS
```python
def _flood_fill(start, obstacles, width, height):
    """Calcula cuánto espacio libre existe desde una posición"""
    visited = set()
    queue = deque([start])
    count = 0
    
    while queue:
        cell = queue.popleft()
        count += 1
        
        for neighbor in (cell + UP, cell + DOWN, cell + LEFT, cell + RIGHT):
            if neighbor not in visited and neighbor not in obstacles:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return count  # Número de celdas libres conectadas
```

**¿Qué detecta?**
- Calcula el área libre desde tu posición actual
- Si hay < tu tamaño de cuerpo, estás atrapado
- Previene quedarse encerrado

**Analogía:**
- El Xenomorfo siente cuánto espacio hay para maniobrar
- Si el pasillo es muy estrecho y hay enemigos, se retira

---

### 9. `_wall_distance()` - EL INSTINTO PARÁSITA
```python
def _wall_distance(position, width, height):
    """Calcula la distancia mínima a cualquier pared"""
    x, y = position
    return min(x, y, width - 1 - x, height - 1 - y)
```

**¿Por qué es genial?**
- Cuando todos los movimientos son igual de seguros, **prefiere estar cerca de la pared**
- Es la heurística de "pegarse a la pared" de los 90s
- Solo tienes 4 giros posibles en los lados: mucho más fácil de controlar

**Analogía:**
- El Xenomorfo usa las paredes como soporte defensivo
- No se adentra en espacios abiertos sin ventaja

---

## 🍖 SISTEMA DE SUBSISTENCIA

### 10. `_get_closest_food()` - EL BUSCADOR DE RECURSOS
```python
def _get_closest_food(start, foods, obstacles, width, height):
    """Encuentra la comida más cercana (en pasos, no en línea recta)"""
    closest = None
    min_dist = infinity
    
    for food in foods:
        dist = _bfs_distance(start, food, obstacles, width, height)
        if dist < min_dist:
            min_dist = dist
            closest = food
    
    return closest
```

**¿Por qué BFS y no distancia euclidiana?**
- BFS calcula pasos reales
- Distancia euclidiana (línea recta) no funciona si hay obstáculos
- Es como el Xenomorfo que sabe navegar mazmorras, no vuela en línea recta

---

### 11. `_reconstruct_body_chain()` - EL DETECTIVE DE CUERPOS
```python
def _reconstruct_body_chain(head, body_parts):
    """Ordena los segmentos del cuerpo en secuencia real"""
    chain = [head]
    unattached = body_parts
    
    while unattached:
        current = chain[-1]
        for part in unattached:
            if manhattan_distance(part, current) == 1:
                chain.append(part)
                unattached.remove(part)
                break
    
    return chain  # Cabeza → cuello → cuerpo → cola
```

**¿Por qué es crítico?**
- El tablero ASCII muestra los segmentos desordenados
- Si no reconstruyes la cadena, no sabes quién es la cola
- El tablero podría ser:
  ```
  |a*A|
  |aaa|
  ```
  ¿Es (0,0)→(2,0)→... o (2,0)→(0,0)→...?

**Analogía:**
- El Xenomorfo "sabe" qué es la cabeza, qué es la cola
- Si confundes el cuerpo del enemigo, te matan

---

## 📊 MATRIZ DE DECISIÓN COMPLETA

```
┌─────────────────────────────────────────────────────────────┐
│                    TURNO DE JUEGO                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                   ¿TENGO CUERPO? (my_body)
                    │              │
                    NO             SÍ
                    │              │
            Return RIGHT      ▼
                        CONSTRUIR MAPA DEFENSIVO
                        ├─ my_obstacles (mi cuerpo)
                        ├─ enemy_obstacles (su cuerpo)
                        ├─ enemy_danger_zones (su cabeza+4)
                        └─ forbidden_dir (giro 180°)
                              │
                              ▼
                        GENERAR MOVIMIENTOS VÁLIDOS
                        ├─ Dentro del tablero
                        ├─ No choquen conmigo
                        ├─ No sean giro 180°
                        └─ No sean cola si hay comida
                              │
                              ▼
                        ¿HAY MOVIMIENTOS?
                        │              │
                        NO             SÍ
                        │              │
                Return RANDOM   ▼
                        FILTRAR POR SEGURIDAD (Flood Fill)
                        └─ safe_moves (con espacio suficiente)
                              │
                              ▼
                        ¿SOY MÁS GRANDE QUE ENEMIGO?
                        │              │
                        NO             SÍ
                        │              │
                        │         ▼
                        │    PERSEGUIR COLA ENEMIGA
                        │    └─ _find_enemy_tail_move()
                        │         │
                        │         ▼
                        │    ¿PUEDO ALCANZAR?
                        │    │              │
                        │    NO             SÍ
                        │    │              │
                        │    ▼          Return ATAQUE
                        │    
                        ▼
                        INTENTAR TRAMPA
                        └─ _find_intercept_move()
                             │
                             ▼
                        ¿PUEDO ACORRALAR?
                        │              │
                        NO             SÍ
                        │              │
                        ▼          Return TRAMPA
                        BUSCAR COMIDA
                        ├─ _get_closest_food()
                        ├─ _bfs_best_move()
                        └─ Validar espacio post-crecimiento
                             │
                             ▼
                        ¿COMIDA SEGURA?
                        │              │
                        NO             SÍ
                        │              │
                        ▼          Return COMIDA
                        SUPERVIVENCIA (Wall-Hugging)
                        ├─ Máximo espacio libre
                        ├─ Priorizar cercanía a pared
                        └─ Return SEGURO
```

---

## 🦾 COMPARACIÓN CON ALIEN ISOLATION

| Aspecto | Alien Isolation | Dev Sentinel Bot |
|---------|-----------------|------------------|
| **Percepción** | Ve y oye a la presa | Parsea el tablero y detecta posiciones |
| **Acecho** | Sigue desde sombras | Detecta si enemigo es más pequeño |
| **Ataque Coordinado** | Corta rutas de escape | `_find_intercept_move()` bloquea salidas |
| **Persecución Inteligente** | Persigue al jugador | `_find_enemy_tail_move()` con BFS |
| **Evitar Peligro** | Evita soldados armados | Evita enemigos ≥ su tamaño |
| **Adaptabilidad** | Cambia estrategia según enemigos | Cambia a ofensiva/defensa según tamaño |
| **Eficiencia** | Movimiento óptimo | BFS garantiza el camino más corto |
| **Supervivencia** | Conoce sus límites | Flood Fill detecta trampas |

---

## 🎓 RESUMEN: POR QUÉ ES DEPREDADOR

1. **Percepción Perfecta**: Sabe exactamente dónde está todo (enemigo, comida, paredes)
2. **Decisiones Jerárquicas**: Ataca primero, come después, escapa último
3. **Oportunismo**: Si eres más pequeño, TE PERSIGUE
4. **Eficiencia Matemática**: BFS garantiza caminos óptimos
5. **Detección de Trampas**: Flood Fill identifica espacios seguros
6. **Adaptabilidad**: Cambia estrategia según la situación
7. **Disciplina**: Nunca hace giros 180°, siempre mantiene escapes
8. **Instinto de Supervivencia**: Wall-hugging cuando todo falla

**El resultado:** Un bot que es como el Xenomorfo: silencioso, imparable, oportunista, y cuando decides atacar, va por la garganta.

