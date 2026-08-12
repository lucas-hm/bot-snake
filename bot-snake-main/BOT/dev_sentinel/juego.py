import sys
import pygame # type: ignore

class VisualizadorPygame:
    def __init__(self, ancho_grid=20, alto_grid=20):
        pygame.init() # type: ignore
        # Definir colores
        self.COLOR_FONDO = (20, 20, 20)
        self.COLOR_MANZANA = (255, 50, 50)  # Rojo
        self.COLOR_DEV = (0, 230, 0)      # Verde
        self.COLOR_RIVAL = (50, 150, 255)   # Azul
        self.COLOR_COLA_PEQUENA = (255, 0, 0) # Rojo intenso para la cola

        # Configuración de pantalla para 1920x1080
        self.ancho_pantalla = 1920
        self.alto_pantalla = 1080
        
        # Calcular tamaño de celda para ocupar la mayor parte de la pantalla 
        # manteniendo las proporciones del grid.
        self.tam_celda = min(self.ancho_pantalla // ancho_grid, self.alto_pantalla // alto_grid)
        
        # Centrar el grid en la pantalla
        self.margen_x = (self.ancho_pantalla - (ancho_grid * self.tam_celda)) // 2
        self.margen_y = (self.alto_pantalla - (alto_grid * self.tam_celda)) // 2

        self.screen = pygame.display.set_mode((self.ancho_pantalla, self.alto_pantalla)) # type: ignore
        pygame.display.set_caption("Partida Bot Snake - dev_sentinel") # type: ignore
        self.clock = pygame.time.Clock() # type: ignore

    def renderizar(self, estado):
        # Procesar eventos para evitar que la ventana se congele
        for event in pygame.event.get(): # type: ignore
            if event.type == pygame.QUIT: # type: ignore
                pygame.quit() # type: ignore
                sys.exit()

        self.screen.fill(self.COLOR_FONDO)  # Fondo oscuro

        # Dibujar Manzana
        if "apple" in estado:
            ax, ay = estado["apple"]
            pygame.draw.rect( # type: ignore
                self.screen,
                self.COLOR_MANZANA,
                (
                    self.margen_x + ax * self.tam_celda,
                    self.margen_y + ay * self.tam_celda,
                    self.tam_celda,
                    self.tam_celda,
                ),
            )

        # Obtener cuerpos de las serpientes
        cuerpo_dev = estado.get("dev_sentinel", [])
        cuerpo_rival = estado.get("rival_bot", [])

        len_dev = len(cuerpo_dev)
        len_rival = len(cuerpo_rival)

        # Determinar cuál es más pequeña (si tienen longitud distinta)
        serpiente_pequena = None
        if len_dev > 0 and len_rival > 0:
            if len_dev < len_rival:
                serpiente_pequena = "dev_sentinel"
            elif len_rival < len_dev:
                serpiente_pequena = "rival_bot"

        # Dibujar dev_sentinel (Verde)
        for i, segment in enumerate(cuerpo_dev):
            color = self.COLOR_DEV
            # Si es la más pequeña y es el último segmento (la cola)
            if serpiente_pequena == "dev_sentinel" and i == len_dev - 1 and len_dev > 1:
                 color = self.COLOR_COLA_PEQUENA

            pygame.draw.rect( # type: ignore
                self.screen,
                color,
                (
                    self.margen_x + segment[0] * self.tam_celda,
                    self.margen_y + segment[1] * self.tam_celda,
                    self.tam_celda,
                    self.tam_celda,
                ),
            )

        # Dibujar Bot Rival (Azul)
        for i, segment in enumerate(cuerpo_rival):
            color = self.COLOR_RIVAL
            # Si es la más pequeña y es el último segmento (la cola)
            if serpiente_pequena == "rival_bot" and i == len_rival - 1 and len_rival > 1:
                color = self.COLOR_COLA_PEQUENA

            pygame.draw.rect( # type: ignore
                self.screen,
                color,
                (
                    self.margen_x + segment[0] * self.tam_celda,
                    self.margen_y + segment[1] * self.tam_celda,
                    self.tam_celda,
                    self.tam_celda,
                ),
            )

        pygame.display.flip() # type: ignore
        self.clock.tick(60)  # Limitar la velocidad a 10 FPS / turnos por segundo

# Ejemplo de uso (puedes integrar esto en tu script de ejecución):
# if __name__ == "__main__":
#     # Supongamos un grid de 40x30
#     visualizador = VisualizadorPygame(ancho_grid=40, alto_grid=30)
    
#     # Estado de ejemplo donde dev_sentinel es más pequeña
#     estado_ejemplo = {
#         "apple": (15, 10),
#         "dev_sentinel": [(5, 5), (5, 6), (5, 7)], # Longitud 3
#         "rival_bot": [(20, 20), (20, 21), (20, 22), (20, 23)] # Longitud 4
#     }
    
#     running = True
#     while running:
#         visualizador.renderizar(estado_ejemplo)
#         # Aquí iría la lógica para actualizar el estado_ejemplo en cada turno