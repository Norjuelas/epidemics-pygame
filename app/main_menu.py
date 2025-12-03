import pygame
import random

class MainMenu:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.bg_color = (20, 20, 30)
        self.text_color = (255, 255, 255)
        self.btn_color = (0, 100, 200)
        self.btn_hover = (0, 150, 250)
        
        try:
            self.bg_image = pygame.image.load("images/menu.png").convert()
            self.bg_image = pygame.transform.scale(self.bg_image, self.screen_size)
        except pygame.error:
            self.bg_image = None
        
        self.font_large = pygame.font.SysFont("Arial", 60, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 32)
        
        self.num_players = 2
        self.seed_input = "42"
        self.entering_seed = False
        
        # UI Elements
        self.buttons = {}
        cx = screen_size[0] // 2
        cy = screen_size[1] // 2
        
        self.buttons["2p"] = pygame.Rect(cx - 150, cy - 80, 80, 50)
        self.buttons["3p"] = pygame.Rect(cx - 40, cy - 80, 80, 50)
        self.buttons["4p"] = pygame.Rect(cx + 70, cy - 80, 80, 50)
        
        # Seed Input Area
        self.seed_rect = pygame.Rect(cx - 100, cy + 10, 200, 40)
        self.buttons["random_seed"] = pygame.Rect(cx + 120, cy + 10, 120, 40)
        
        self.buttons["start"] = pygame.Rect(cx - 100, cy + 80, 200, 60)
        self.buttons["exit"] = pygame.Rect(cx - 100, cy + 160, 200, 60)
        
        self.finished = False
        self.selected_action = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return # Only left click
            # Seed Input Focus
            if self.seed_rect.collidepoint(event.pos):
                self.entering_seed = True
            else:
                self.entering_seed = False

            for key, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    if key == "2p": self.num_players = 2
                    elif key == "3p": self.num_players = 3
                    elif key == "4p": self.num_players = 4
                    elif key == "random_seed":
                        self.seed_input = str(random.randint(1, 9999))
                    elif key == "start":
                        self.selected_action = "start"
                        self.finished = True
                    elif key == "exit":
                        self.selected_action = "exit"
                        self.finished = True
        
        if event.type == pygame.KEYDOWN and self.entering_seed:
            if event.key == pygame.K_BACKSPACE:
                self.seed_input = self.seed_input[:-1]
            elif event.unicode.isnumeric():
                self.seed_input += event.unicode

    def draw(self, screen):
        if self.bg_image:
            screen.blit(self.bg_image, (0, 0))
        else:
            screen.fill(self.bg_color)
        
        # --- Changed Game Title ---
        if not self.bg_image: 
            title = self.font_large.render("EPIDEMICS", True, (255, 50, 50))
            screen.blit(title, (self.screen_size[0]//2 - title.get_width()//2, 80))
        
        sub = self.font_medium.render("Jugadores:", True, self.text_color)
        screen.blit(sub, (self.screen_size[0]//2 - sub.get_width()//2, 280))
        
        mouse_pos = pygame.mouse.get_pos()
        
        for k in ["2p", "3p", "4p"]:
            rect = self.buttons[k]
            is_selected = (int(k[0]) == self.num_players)
            color = (0, 200, 100) if is_selected else (50, 50, 50)
            pygame.draw.rect(screen, color, rect, border_radius=5)
            text = self.font_medium.render(k[0], True, self.text_color)
            screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))

        # Seed Drawing
        col = (200, 200, 255) if self.entering_seed else (100, 100, 100)
        pygame.draw.rect(screen, col, self.seed_rect, 2)
        txt = self.font_medium.render(f"Semilla: {self.seed_input}", True, (255,255,255))
        screen.blit(txt, (self.seed_rect.x + 10, self.seed_rect.y + 5))
        
        # Random Button
        rr = self.buttons["random_seed"]
        pygame.draw.rect(screen, (50, 50, 80), rr, border_radius=5)
        rt = self.font_medium.render("Aleatoria", True, (200,200,200))
        screen.blit(rt, (rr.centerx - rt.get_width()//2, rr.centery - rt.get_height()//2))

        # Start/Exit
        r_start = self.buttons["start"]
        c_start = self.btn_hover if r_start.collidepoint(mouse_pos) else self.btn_color
        pygame.draw.rect(screen, c_start, r_start, border_radius=10)
        t_start = self.font_medium.render("INICIAR", True, self.text_color)
        screen.blit(t_start, (r_start.centerx - t_start.get_width()//2, r_start.centery - t_start.get_height()//2))

        r_exit = self.buttons["exit"]
        c_exit = (150, 50, 50) if r_exit.collidepoint(mouse_pos) else (100, 30, 30)
        pygame.draw.rect(screen, c_exit, r_exit, border_radius=10)
        t_exit = self.font_medium.render("SALIR", True, self.text_color)
        screen.blit(t_exit, (r_exit.centerx - t_exit.get_width()//2, r_exit.centery - t_exit.get_height()//2))

