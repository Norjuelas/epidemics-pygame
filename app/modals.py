from typing import List
import pygame
from app.config import EVENT_NAMES

class CitySelectionModal:
    def __init__(self, title: str, cities: List[str], game_ref, callback_confirm, callback_cancel):
        self.title = title
        self.cities = cities
        self.game = game_ref
        self.on_confirm = callback_confirm
        self.on_cancel = callback_cancel
        self.width = 900
        self.height = 600
        self.bg_color = (30, 30, 40)
        self.border_color = (100, 100, 100)
        
        self.scroll_y = 0
        self.cols = 4
        self.item_width = 200
        self.item_height = 40
        self.padding = 20
        self.start_x = 50
        self.start_y = 100
        
        rows = (len(cities) + self.cols - 1) // self.cols
        self.content_height = max(0, rows * (self.item_height + 10) - (self.height - 200))
        
        self.city_buttons = []
        for i, city_name in enumerate(self.cities):
            col = i % self.cols
            row = i // self.cols
            x = self.start_x + col * (self.item_width + 10)
            y = self.start_y + row * (self.item_height + 10)
            rect = pygame.Rect(x, y, self.item_width, self.item_height)
            self.city_buttons.append({"name": city_name, "rect": rect})
            
        self.cancel_rect = pygame.Rect(self.width // 2 - 100, self.height - 60, 200, 40)

    def handle_event(self, event, offset_x, offset_y):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 20
            self.scroll_y = max(0, min(self.scroll_y, self.content_height))
            return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return False 
            
            mouse_pos = event.pos
            rel_x = mouse_pos[0] - offset_x
            rel_y = mouse_pos[1] - offset_y
            
            if self.cancel_rect.collidepoint(rel_x, rel_y):
                self.on_cancel()
                return True
            
            for btn in self.city_buttons:
                visual_rect = btn["rect"].copy()
                visual_rect.y -= self.scroll_y
                
                if visual_rect.y < 80 or visual_rect.y > self.height - 80:
                    continue
                    
                if visual_rect.collidepoint(rel_x, rel_y):
                    self.on_confirm(btn["name"])
                    return True
        return False

    def draw(self, screen, screen_center):
        modal_x = screen_center[0] - self.width // 2
        modal_y = screen_center[1] - self.height // 2
        modal_surface = pygame.Surface((self.width, self.height))
        modal_surface.fill(self.bg_color)
        pygame.draw.rect(modal_surface, self.border_color, (0, 0, self.width, self.height), 3)
        
        font_title = pygame.font.SysFont("Arial", 28, bold=True)
        title_surf = font_title.render(self.title, True, (255, 255, 255))
        modal_surface.blit(title_surf, (self.width//2 - title_surf.get_width()//2, 30))
        
        clip_rect = pygame.Rect(0, 80, self.width, self.height - 150)
        modal_surface.set_clip(clip_rect)
        
        font_btn = pygame.font.SysFont("Arial", 16)
        mouse_pos = pygame.mouse.get_pos()
        rel_mouse_x = mouse_pos[0] - modal_x
        rel_mouse_y = mouse_pos[1] - modal_y
        
        hovered_city_data = None
        
        for btn in self.city_buttons:
            rect = btn["rect"].copy()
            rect.y -= self.scroll_y
            
            if rect.bottom < 80 or rect.top > self.height - 70:
                continue 
                
            is_hovered = rect.collidepoint(rel_mouse_x, rel_mouse_y)
            color = (60, 60, 80) if not is_hovered else (100, 100, 150)
            pygame.draw.rect(modal_surface, color, rect)
            pygame.draw.rect(modal_surface, (150, 150, 150), rect, 1)
            text_surf = font_btn.render(btn["name"], True, (220, 220, 220))
            modal_surface.blit(text_surf, (rect.x + 10, rect.y + 10))
            if is_hovered:
                hovered_city_data = self.game.cities.get(btn["name"].lower())
        
        modal_surface.set_clip(None) 
        
        pygame.draw.rect(modal_surface, (150, 50, 50), self.cancel_rect)
        cancel_text = font_btn.render("CANCELAR", True, (255, 255, 255))
        modal_surface.blit(cancel_text, (self.cancel_rect.centerx - cancel_text.get_width()//2, self.cancel_rect.centery - cancel_text.get_height()//2))
        
        screen.blit(modal_surface, (modal_x, modal_y))
        if hovered_city_data:
            self._draw_tooltip(screen, mouse_pos, hovered_city_data)

    def _draw_tooltip(self, screen, pos, city_obj):
        font_tip = pygame.font.SysFont("Arial", 14)
        info_lines = [
            f"Color: {city_obj.color}",
            f"Infecciones: {city_obj.infections}",
            f"Estación: {'Sí' if city_obj.name in self.game.research_stations else 'No'}"
        ]
        w, h = 160, 20 + len(info_lines) * 18
        x, y = pos[0] + 15, pos[1] + 15
        if x + w > screen.get_width(): x -= (w + 20)
        pygame.draw.rect(screen, (20, 20, 20), (x, y, w, h))
        pygame.draw.rect(screen, (200, 200, 200), (x, y, w, h), 1)
        for i, line in enumerate(info_lines):
            t_surf = font_tip.render(line, True, (255, 255, 255))
            screen.blit(t_surf, (x + 10, y + 10 + i * 18))

class ResilientModal:
    def __init__(self, game, callback_confirm, callback_cancel):
        self.game = game
        self.on_confirm = callback_confirm
        self.on_cancel = callback_cancel
        self.width = 600
        self.height = 500
        self.cards = self.game.infection_deck.discard_pile
        self.selected_card = None
        self.confirm_rect = pygame.Rect(250, 430, 100, 40)
        self.cancel_rect = pygame.Rect(250, 10, 100, 30)

    def handle_event(self, event, ox, oy):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return False
            mx, my = event.pos
            rx, ry = mx - ox, my - oy
            if self.cancel_rect.collidepoint(rx, ry):
                self.on_cancel()
                return True
            if self.selected_card and self.confirm_rect.collidepoint(rx, ry):
                self.on_confirm(self.selected_card)
                return True
            
            start_x, start_y = 30, 50
            for i, card in enumerate(self.cards):
                col = i % 3
                row = i // 3
                r = pygame.Rect(start_x + col*180, start_y + row*40, 170, 35)
                if r.collidepoint(rx, ry):
                    self.selected_card = card
        return False

    def draw(self, screen, center):
        ox, oy = center[0]-self.width//2, center[1]-self.height//2
        surf = pygame.Surface((self.width, self.height))
        surf.fill((30,30,40))
        pygame.draw.rect(surf, (100,100,100), (0,0,self.width,self.height), 2)
        
        f = pygame.font.SysFont("Arial", 16)
        t = f.render("Seleccionar Carta para Eliminar (Resiliente)", True, (255,255,255))
        surf.blit(t, (20, 10))
        
        start_x, start_y = 30, 50
        for i, card in enumerate(self.cards):
            col = i % 3
            row = i // 3
            r = pygame.Rect(start_x + col*180, start_y + row*40, 170, 35)
            color = (0, 100, 0) if card == self.selected_card else (60,60,60)
            pygame.draw.rect(surf, color, r)
            c_txt = f.render(card, True, (200,200,200))
            surf.blit(c_txt, (r.x+5, r.y+5))
            
        if self.selected_card:
            pygame.draw.rect(surf, (0,150,0), self.confirm_rect)
            conf = f.render("CONFIRMAR", True, (255,255,255))
            surf.blit(conf, (self.confirm_rect.x+5, self.confirm_rect.y+10))
            
        screen.blit(surf, (ox, oy))

class ForecastModal:
    def __init__(self, game, callback_confirm, callback_cancel):
        self.game = game
        self.on_confirm = callback_confirm
        self.on_cancel = callback_cancel
        self.width = 400
        self.height = 500
        self.top_cards = list(self.game.infection_deck.peek_top(6))
        self.selected_idx = None 
        self.confirm_rect = pygame.Rect(150, 450, 100, 40)

    def handle_event(self, event, ox, oy):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return False
            mx, my = event.pos
            rx, ry = mx - ox, my - oy
            
            if self.confirm_rect.collidepoint(rx, ry):
                self.on_confirm(self.top_cards)
                return True
                
            start_y = 60
            for i, card in enumerate(self.top_cards):
                r = pygame.Rect(50, start_y + i*50, 300, 40)
                if r.collidepoint(rx, ry):
                    if self.selected_idx is None:
                        self.selected_idx = i
                    else:
                        self.top_cards[self.selected_idx], self.top_cards[i] = self.top_cards[i], self.top_cards[self.selected_idx]
                        self.selected_idx = None
        return False

    def draw(self, screen, center):
        ox, oy = center[0]-self.width//2, center[1]-self.height//2
        surf = pygame.Surface((self.width, self.height))
        surf.fill((30,30,40))
        pygame.draw.rect(surf, (100,100,100), (0,0,self.width,self.height), 2)
        
        f = pygame.font.SysFont("Arial", 16)
        t = f.render("Reordenar (Click 1o, Click 2o para cambiar)", True, (255,255,255))
        surf.blit(t, (20, 20))
        
        start_y = 60
        for i, card in enumerate(self.top_cards):
            r = pygame.Rect(50, start_y + i*50, 300, 40)
            color = (100, 100, 0) if i == self.selected_idx else (60,60,80)
            pygame.draw.rect(surf, color, r)
            txt = f.render(f"{i+1}. {card}", True, (255,255,255))
            surf.blit(txt, (r.x+10, r.y+10))
            
        pygame.draw.rect(surf, (0,150,0), self.confirm_rect)
        c_t = f.render("CONFIRMAR", True, (255,255,255))
        surf.blit(c_t, (self.confirm_rect.x+5, self.confirm_rect.y+10))
        screen.blit(surf, (ox, oy))

class AirliftModal:
    def __init__(self, game, callback_confirm, callback_cancel):
        self.game = game
        self.on_confirm = callback_confirm
        self.on_cancel = callback_cancel
        self.width = 900
        self.height = 600
        self.selected_player_idx = None
        self.city_modal = CitySelectionModal("Seleccionar Destino (Puente Aéreo)", 
                                             [c.name for c in game.cities.values()], 
                                             game, self._on_city_selected, callback_cancel)
        self.step = 1

    def _on_city_selected(self, city_name):
        self.on_confirm(self.selected_player_idx, city_name)

    def handle_event(self, event, ox, oy):
        if self.step == 2:
            return self.city_modal.handle_event(event, ox, oy)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return False
            mx, my = event.pos
            rx, ry = mx - ox, my - oy
            start_x = 50
            for i, p in enumerate(self.game.players):
                r = pygame.Rect(start_x, 100, 150, 50)
                if r.collidepoint(rx, ry):
                    self.selected_player_idx = i
                    self.step = 2
                    return False
                start_x += 160
        return False

    def draw(self, screen, center):
        if self.step == 2:
            self.city_modal.draw(screen, center)
            return

        ox, oy = center[0]-self.width//2, center[1]-self.height//2
        surf = pygame.Surface((self.width, self.height))
        surf.fill((30,30,40))
        pygame.draw.rect(surf, (100,100,100), (0,0,self.width,self.height), 2)
        
        f = pygame.font.SysFont("Arial", 22)
        t = f.render("Puente Aéreo: Seleccionar Jugador", True, (255,255,255))
        surf.blit(t, (30, 30))
        
        start_x = 50
        for i, p in enumerate(self.game.players):
            r = pygame.Rect(start_x, 100, 150, 50)
            pygame.draw.rect(surf, (0,100,200), r)
            txt = f.render(p.name, True, (255,255,255))
            surf.blit(txt, (r.x+10, r.y+15))
            start_x += 160
            
        screen.blit(surf, (ox, oy))

class ShareKnowledgeModal:
    def __init__(self, game_ref, callback_confirm, callback_cancel, current_location=None, current_hand=None):
        self.game = game_ref
        self.on_confirm = callback_confirm
        self.on_cancel = callback_cancel
        self.width = 900
        self.height = 600
        self.bg_color = (30, 30, 40)
        self.border_color = (100, 100, 100)
        
        self.current_player = self.game.players[self.game.current_player_index]
        # Usar la ubicación y mano virtual si se proporcionan (acciones planificadas)
        self.location = current_location if current_location else self.current_player.location
        self.player_hand = current_hand if current_hand is not None else self.current_player.hand
        
        self.available_players = [
            p for p in self.game.players 
            if p != self.current_player and p.location == self.location
        ]
        
        self.selected_target_player = None
        self.selected_card = None 
        self.close_rect = pygame.Rect(self.width - 40, 10, 30, 30)
        self.confirm_rect = pygame.Rect(self.width // 2 - 60, self.height - 50, 120, 40)

    def handle_event(self, event, offset_x, offset_y):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return False
            mouse_pos = event.pos
            rel_x = mouse_pos[0] - offset_x
            rel_y = mouse_pos[1] - offset_y
            
            if self.close_rect.collidepoint(rel_x, rel_y):
                self.on_cancel()
                return True
                
            if self.selected_card and self.selected_target_player and self.confirm_rect.collidepoint(rel_x, rel_y):
                card_name, owner = self.selected_card
                if owner == self.current_player:
                    if self.game.transfer_card(self.current_player, self.selected_target_player, card_name):
                         self.on_confirm("share", f"Dio {card_name} a {self.selected_target_player.name}")
                else:
                    if self.game.transfer_card(self.selected_target_player, self.current_player, card_name):
                         self.on_confirm("share", f"Recibió {card_name} de {self.selected_target_player.name}")
                return True
            
            start_x = 50
            for p in self.available_players:
                r = pygame.Rect(start_x, 60, 150, 40)
                if r.collidepoint(rel_x, rel_y):
                    self.selected_target_player = p
                    self.selected_card = None 
                start_x += 160
            
            if self.selected_target_player:
                base_y = 150
                # Usar self.player_hand (mano virtual)
                for i, card in enumerate(self.player_hand):
                    r = pygame.Rect(50 + i * 110, base_y + 30, 100, 40)
                    if r.collidepoint(rel_x, rel_y):
                         if card.lower() == self.location.lower(): 
                             self.selected_card = (card, self.current_player)
                
                base_y = 300
                # Mano del otro jugador (asumimos que no cambia en planificación)
                for i, card in enumerate(self.selected_target_player.hand):
                    r = pygame.Rect(50 + i * 110, base_y + 30, 100, 40)
                    if r.collidepoint(rel_x, rel_y):
                         if card.lower() == self.location.lower(): 
                             self.selected_card = (card, self.selected_target_player)
        return False

    def draw(self, screen, screen_center):
        modal_x = screen_center[0] - self.width // 2
        modal_y = screen_center[1] - self.height // 2
        modal_surface = pygame.Surface((self.width, self.height))
        modal_surface.fill(self.bg_color)
        pygame.draw.rect(modal_surface, self.border_color, (0, 0, self.width, self.height), 3)

        font_title = pygame.font.SysFont("Arial", 22, bold=True)
        font_text = pygame.font.SysFont("Arial", 16)
        
        t = font_title.render(f"Compartir Conocimiento en {self.location}", True, (255, 255, 255))
        modal_surface.blit(t, (20, 20))
        
        pygame.draw.rect(modal_surface, (200, 50, 50), self.close_rect)
        x_char = font_text.render("X", True, (255, 255, 255))
        modal_surface.blit(x_char, (self.close_rect.centerx - x_char.get_width()//2, self.close_rect.centery - x_char.get_height()//2))
        
        if not self.available_players:
            msg = font_text.render("No hay otros jugadores en esta ciudad (planificada).", True, (200, 200, 200))
            modal_surface.blit(msg, (50, 100))
            screen.blit(modal_surface, (modal_x, modal_y))
            return

        # Draw Player Selectors
        start_x = 50
        lbl = font_text.render("1. Selecciona Jugador:", True, (200, 200, 200))
        modal_surface.blit(lbl, (50, 40))
        
        for p in self.available_players:
            r = pygame.Rect(start_x, 60, 150, 40)
            col = (0, 100, 200) if self.selected_target_player == p else (50, 50, 60)
            pygame.draw.rect(modal_surface, col, r)
            pygame.draw.rect(modal_surface, (150, 150, 150), r, 1)
            txt = font_text.render(p.name, True, (255, 255, 255))
            modal_surface.blit(txt, (r.centerx - txt.get_width()//2, r.centery - txt.get_height()//2))
            start_x += 160
            
        if self.selected_target_player:
            # Current Player Hand (Virtual)
            y_base = 150
            lbl = font_text.render(f"Tu Mano (Dar carta '{self.location}'):", True, (200, 200, 200))
            modal_surface.blit(lbl, (50, y_base))
            
            for i, card in enumerate(self.player_hand):
                r = pygame.Rect(50 + i * 110, y_base + 30, 100, 40)
                is_valid = (card.lower() == self.location.lower())
                is_sel = (self.selected_card == (card, self.current_player))
                col = (0, 150, 0) if is_sel else ((100, 100, 120) if is_valid else (40, 40, 50))
                
                pygame.draw.rect(modal_surface, col, r)
                pygame.draw.rect(modal_surface, (100, 100, 100), r, 1)
                
                txt_col = (255, 255, 255) if is_valid else (100, 100, 100)
                c_txt = font_text.render(card[:9], True, txt_col)
                modal_surface.blit(c_txt, (r.x + 5, r.y + 10))

            # Target Player Hand
            y_base = 300
            lbl = font_text.render(f"Mano de {self.selected_target_player.name} (Tomar carta '{self.location}'):", True, (200, 200, 200))
            modal_surface.blit(lbl, (50, y_base))
            
            for i, card in enumerate(self.selected_target_player.hand):
                r = pygame.Rect(50 + i * 110, y_base + 30, 100, 40)
                is_valid = (card.lower() == self.location.lower())
                is_sel = (self.selected_card == (card, self.selected_target_player))
                col = (0, 150, 0) if is_sel else ((100, 100, 120) if is_valid else (40, 40, 50))
                
                pygame.draw.rect(modal_surface, col, r)
                pygame.draw.rect(modal_surface, (100, 100, 100), r, 1)
                
                txt_col = (255, 255, 255) if is_valid else (100, 100, 100)
                c_txt = font_text.render(card[:9], True, txt_col)
                modal_surface.blit(c_txt, (r.x + 5, r.y + 10))

            if self.selected_card:
                col = (0, 200, 0)
                pygame.draw.rect(modal_surface, col, self.confirm_rect)
                txt = font_title.render("CONFIRMAR", True, (255, 255, 255))
                modal_surface.blit(txt, (self.confirm_rect.centerx - txt.get_width()//2, self.confirm_rect.centery - txt.get_height()//2))

        screen.blit(modal_surface, (modal_x, modal_y))

class DiscardModal:
    def __init__(self, game_ref, callback_discard):
        self.game = game_ref
        self.on_discard = callback_discard
        self.width = 700
        self.height = 300
        self.bg_color = (40, 30, 30) # Dark red hint
        self.border_color = (200, 100, 100)
        
        self.player = self.game.players[self.game.current_player_index]
        self.hand = self.player.hand
        self.selected_card = None
        self.confirm_rect = pygame.Rect(self.width // 2 - 60, self.height - 50, 120, 40)

    def handle_event(self, event, offset_x, offset_y):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return False
            mouse_pos = event.pos
            rel_x = mouse_pos[0] - offset_x
            rel_y = mouse_pos[1] - offset_y

            # Check cards
            start_x = 50
            for i, card in enumerate(self.hand):
                r = pygame.Rect(start_x + i * 85, 100, 80, 50)
                if r.collidepoint(rel_x, rel_y):
                    self.selected_card = card
            
            # Check confirm
            if self.selected_card and self.confirm_rect.collidepoint(rel_x, rel_y):
                self.on_discard(self.selected_card)
                return True
        return False

    def draw(self, screen, screen_center):
        modal_x = screen_center[0] - self.width // 2
        modal_y = screen_center[1] - self.height // 2
        modal_surface = pygame.Surface((self.width, self.height))
        modal_surface.fill(self.bg_color)
        pygame.draw.rect(modal_surface, self.border_color, (0, 0, self.width, self.height), 3)

        font_title = pygame.font.SysFont("Arial", 22, bold=True)
        font_text = pygame.font.SysFont("Arial", 16)
        
        t = font_title.render(f"¡Límite de Mano Excedido! ({len(self.hand)}/7)", True, (255, 200, 200))
        modal_surface.blit(t, (self.width//2 - t.get_width()//2, 20))
        
        st = font_text.render("Selecciona una carta para descartar:", True, (200, 200, 200))
        modal_surface.blit(st, (self.width//2 - st.get_width()//2, 50))
        
        start_x = 50
        for i, card in enumerate(self.hand):
            r = pygame.Rect(start_x + i * 85, 100, 80, 50)
            is_sel = (card == self.selected_card)
            
            # Get Color
            color = (150, 150, 150)
            if card in EVENT_NAMES:
                color = (50, 205, 50)
            elif card.lower() in self.game.cities:
                 c_obj = self.game.cities[card.lower()]
                 # Mapping colors to RGB
                 c_map = {"Blue": (0,100,200), "Yellow": (200,200,0), "Black": (50,50,50), "Red": (200,0,0)}
                 color = c_map.get(c_obj.color, (100,100,100))
            
            if is_sel:
                pygame.draw.rect(modal_surface, (255, 255, 255), (r.x-2, r.y-2, r.w+4, r.h+4), 2)
            
            pygame.draw.rect(modal_surface, color, r)
            pygame.draw.rect(modal_surface, (0, 0, 0), r, 1)
            
            txt_col = (255,255,255) if color == (50,50,50) else (0,0,0)
            disp = card[:9]
            t_card = font_text.render(disp, True, txt_col)
            modal_surface.blit(t_card, (r.x+5, r.y+15))

        if self.selected_card:
            pygame.draw.rect(modal_surface, (200, 50, 50), self.confirm_rect)
            t_conf = font_title.render("DESCARTAR", True, (255,255,255))
            modal_surface.blit(t_conf, (self.confirm_rect.centerx - t_conf.get_width()//2, self.confirm_rect.centery - t_conf.get_height()//2))

        screen.blit(modal_surface, (modal_x, modal_y))


class PlayerHandsModal:
    def __init__(self, game_ref, callback_close):
        self.game = game_ref
        self.on_close = callback_close
        self.width = 600
        self.height = 400
        self.bg_color = (40, 40, 50)
        self.border_color = (150, 150, 150)
        self.close_rect = pygame.Rect(self.width // 2 - 50, self.height - 50, 100, 30)

    def handle_event(self, event, offset_x, offset_y):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1: return False
            mouse_pos = event.pos
            rel_x = mouse_pos[0] - offset_x
            rel_y = mouse_pos[1] - offset_y
            if self.close_rect.collidepoint(rel_x, rel_y):
                self.on_close()
                return True
        return False

    def draw(self, screen, screen_center):
        modal_x = screen_center[0] - self.width // 2
        modal_y = screen_center[1] - self.height // 2
        modal_surface = pygame.Surface((self.width, self.height))
        modal_surface.fill(self.bg_color)
        pygame.draw.rect(modal_surface, self.border_color, (0, 0, self.width, self.height), 3)

        font_title = pygame.font.SysFont("Arial", 22, bold=True)
        font_text = pygame.font.SysFont("Arial", 16)
        title = font_title.render("Manos de otros jugadores", True, (255, 255, 255))
        modal_surface.blit(title, (self.width // 2 - title.get_width() // 2, 20))

        start_y = 60
        
        for player in self.game.players:
            if player == self.game.players[self.game.current_player_index]:
                continue
            p_text = font_text.render(f"{player.name}: {', '.join(player.hand) if player.hand else 'Vacía'}", True, (200, 200, 220))
            modal_surface.blit(p_text, (30, start_y))
            start_y += 30

        pygame.draw.rect(modal_surface, (150, 50, 50), self.close_rect)
        close_txt = font_text.render("CERRAR", True, (255, 255, 255))
        modal_surface.blit(close_txt, (self.close_rect.centerx - close_txt.get_width() // 2, self.close_rect.centery - close_txt.get_height() // 2))

        screen.blit(modal_surface, (modal_x, modal_y))