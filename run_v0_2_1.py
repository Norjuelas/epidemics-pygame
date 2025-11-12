# runner_v0_2_1.py
from pandemic_v0_2_1 import Game
from typing import List, Tuple, Optional

def main():
    print("=== PANDEMIC v0.2.1 ===")
    game = Game(seed=42)

    # Crear jugadores
    name = input("Nombre del jugador: ")
    game.add_player(name, start_city="Atlanta")
    print(f"\nJugador {name} ha comenzado en Atlanta.\n")

    while not game.game_over:
        player = game.players[game.current_player_index]
        city_obj = game._get_city(player.location)

        print(f"\n=== Turno {game.turn} — {player.name} ===")
        print(f"Ubicación actual: {player.location} ({city_obj.color}) — infecciones: {city_obj.infections}")
        print("Ciudades conectadas:", ", ".join(city_obj.neighbors))

        # Capturar hasta 4 acciones del jugador
        actions: List[Tuple[str, Optional[str]]] = []
        while len(actions) < 4:
            print(f"\nAcción {len(actions)+1}/4")
            cmd = input("Comando (move <ciudad> / cure / infect <ciudad> / conexiones <ciudad> / skip / fin): ").strip().lower()

            if cmd in ("fin", "end"):
                break

            elif cmd.startswith("move "):
                dest = cmd.split(" ", 1)[1].strip().title()
                actions.append(("move", dest))

            elif cmd == "cure":
                actions.append(("cure", None))

            elif cmd.startswith("infect "):
                dest = cmd.split(" ", 1)[1].strip().title()
                actions.append(("infect", dest))

            elif cmd == "skip":
                actions.append(("skip", None))

            elif cmd.startswith("conexiones "):
                base = cmd.split(" ", 1)[1].strip().title()
                base_key = base.lower()
                if base_key in game.cities:
                    neighbors = game.cities[base_key].neighbors
                    print(f"{base} conecta con: {', '.join(neighbors)}")
                else:
                    print("Esa ciudad no existe en el mapa.")
                # No cuenta como acción (solo informativo)

            else:
                print("Comando no reconocido.")

        # Mostrar resumen antes de ejecutar el turno
        print("\n[Resumen de acciones planificadas]")
        for i, (act, arg) in enumerate(actions, 1):
            if arg:
                print(f" {i}. {act} → {arg}")
            else:
                print(f" {i}. {act}")

        confirm = input("\n¿Ejecutar este turno? (s/n): ").strip().lower()
        if confirm != "s":
            print("Turno cancelado. Reiniciando entrada de acciones...")
            continue

        # Ejecutar el turno con la estructura central del juego
        print("\n[run_turn] Ejecutando turno...\n")
        game.run_turn(actions, player_index=game.current_player_index)

        # Mostrar estado resumido
        print("\n--- Estado tras el turno ---")
        print(f"Turno actual: {game.turn}")
        print(f"Jugador actual: {game.players[game.current_player_index].name}")
        print(f"Brotes: {game.outbreaks} | Cartas restantes (PlayerDeck): {len(game.player_deck.deck)}")
        print(f"Cartas restantes (InfectionDeck): {len(game.infection_deck.deck)}")

        cont = input("\n¿Continuar al siguiente turno? (s/n): ").strip().lower()
        if cont != "s":
            print("Saliendo del juego...")
            break

    print(f"\n[FIN DEL JUEGO] Razón: {game.defeat_reason or 'Salida manual.'}")

if __name__ == "__main__":
    main()
