from pandemic_v0_1 import Game

g = Game(seed=20202)        # seed opcional para reproducibilidad
g.add_player("Jugador1", start_city="Atlanta")
g.show_status()

# mover con validación de conexiones
g.move("Atlanta", "Washington")   # si está conectado OK, se mueve y luego se infectan ciudades

# o usar conveniencia (mover desde la ciudad actual del jugador)
g.quick_move("New York")

# curar (trata 1 cubo en la ciudad actual del jugador)
g.quick_cure()

# mostrar estado
g.show_status()
