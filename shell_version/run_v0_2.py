# runner_v0_2.py
from pandemic_v0_2 import Game

def main():
    print("=== PANDEMIC v0.2 ===")
    print("Comandos disponibles:")
    print("  mover <ciudad>   - Mover al jugador actual a una ciudad conectada")
    print("  curar            - Tratar la ciudad actual (remueve 1 infección)")
    print("  estado           - Mostrar estado general del tablero")
    print("  salir            - Terminar la partida\n")

    # Inicializar el juego
    g = Game(seed=42)
    g.add_player("Jugador1", "Atlanta")

    counter = 0

    while True:
        player = g.players[g.current_player_index]
        city = g._get_city(player.location)

        if(counter == 4):
            counter = 0
            g.end_turn()
            

        # Mostrar contexto actual del turno
        print(f"\nTurno {g.turn} — {player.name}")
        print(f"Estás en {city.name} ({city.color}) — infecciones: {city.infections}")
        print("Ciudades conectadas:", ", ".join(city.neighbors))

        # Leer comando
        cmd = input("\n> ").strip().lower()


        if not cmd:
            continue

        if cmd == "salir":
            print("Saliendo del juego...")
            break

        elif cmd.startswith("mover"):
            counter += 1
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                print("Uso: mover <nombre_ciudad>")
                continue
            destino = parts[1]
            try:
                g.move(city.name, destino, player_index=g.current_player_index)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif cmd == "curar":
            counter += 1
            try:
                g.cure(city_name=city.name, player_index=g.current_player_index)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif cmd == "estado":
            g.show_status()

        else:
            print("Comando no reconocido. Usa: mover, curar, estado o salir.")

if __name__ == "__main__":
    main()
