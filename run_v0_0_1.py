# run_pandemic_console.py
from pandemic_v0_1_1 import Game

if __name__ == "__main__":
    g = Game(seed=42)
    g.add_player("Jugador1", "Atlanta")

    print("=== Pandemic v0.1.1 (Consola) ===")
    print("Comandos disponibles:")
    print(" - mover <ciudad>")
    print(" - curar")
    print(" - mostrar")
    print(" - salir")

    while True:
        cmd = input("> ").strip().lower()

        if cmd in ("salir", "exit", "q"):
            print("Saliendo del juego. ¡Gracias por jugar!")
            break

        elif cmd.startswith("mover "):
            _, dest = cmd.split(" ", 1)
            try:
                # Convertir el nombre a formato título, p.ej. "new york" -> "New York"
                g.quick_move(dest.title())
            except Exception as e:
                print(f"[Error] {e}")

        elif cmd == "curar":
            try:
                g.quick_cure()
            except Exception as e:
                print(f"[Error] {e}")

        elif cmd in ("mostrar", "status", "estado"):
            g.show_status()

        else:
            print("Comando no reconocido. Usa: mover <ciudad>, curar, mostrar o salir.")
