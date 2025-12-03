import pygame
import traceback
from app.main_menu import MainMenu
from app.game import Game
from app.pandemic_gui import PandemicGUI

def main():
    pygame.init()
    screen_size = (1280, 800)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("EPIDEMICS (ES)") # --- Changed Game Title in window caption ---
    
    while True:
        menu = MainMenu(screen_size)
        running_menu = True
        while running_menu:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                menu.handle_event(event)
            menu.draw(screen)
            pygame.display.flip()
            if menu.finished:
                if menu.selected_action == "exit":
                    pygame.quit()
                    return
                elif menu.selected_action == "start":
                    running_menu = False
        
        # Use selected seed
        try:
            seed_val = int(menu.seed_input)
        except:
            seed_val = 42

        try:
            print(f"DEBUG: Intentando iniciar Game con seed={seed_val}")
            game = Game(num_players=menu.num_players, seed=seed_val)
            print("DEBUG: Game creado. Iniciando GUI...")
            gui = PandemicGUI(game, screen)
            print("DEBUG: GUI creada. Ejecutando run()...")
            result = gui.run()
        except Exception as e:
            print("\n" * 5)
            print("=" * 50)
            print("CRITICAL PYGAME/ASSET ERROR:")
            print("=" * 50)
            traceback.print_exc()
            print("=" * 50)
            print("EL JUEGO FALLÓ DEBIDO A UN ERROR DE IMAGEN O INICIALIZACIÓN.")
            print("POR FAVOR, REVISA LOS MENSAJES DE 'ADVERTENCIA' ARRIBA EN EL LOG.")
            print("=" * 50)
            print("\n" * 5)
            result = "MENU"
        
        if result == "EXIT":
            break

    pygame.quit()

if __name__ == "__main__":
    main()