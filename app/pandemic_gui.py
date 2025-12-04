import pygame
from app.config import EVENT_DISPLAY_NAMES, EVENT_NAMES
from app.game import Game
from app.modals import (PlayerHandsModal, DiscardModal, ResilientModal,
                        CitySelectionModal, AirliftModal, ForecastModal, ShareKnowledgeModal)
from typing import List, Tuple, Optional

class PandemicGUI:
    def __init__(self, game: Game, screen):
        self.game = game
        self.screen = screen
        self.screen_size = screen.get_size()
        
        # --- Robust Image Loading ---
        def load_image_or_create_fallback(filename: str, size: Tuple[int, int], color: Tuple[int, int] = (255, 0, 255)) -> Optional[pygame.Surface]:
            try:
                img = pygame.image.load(filename).convert_alpha()
                # --- Resize Specifics Requested by User ---
                if 'infection_track_mark.png' in filename:
                     return pygame.transform.scale(img, (309, 38)) 
                
                if filename == 'infection.png':
                    return pygame.transform.scale(img, (70, 70))

                return pygame.transform.scale(img, size)
            except pygame.error:
                print(f"ADVERTENCIA: No se encontró la imagen '{filename}'. Usando fallback.")
                fallback = pygame.Surface(size, pygame.SRCALPHA)
                fallback.fill(color)
                return fallback

        # 1. Map and Menu Backgrounds
        self.map_image = load_image_or_create_fallback("images/map.png", self.screen_size, (20, 20, 50))

        # 2. Player Images
        self.player_images = []
        for i in range(1, 5):
            img = load_image_or_create_fallback(f"images/ficha{i}.png", (16, 30), (255, 255, 255, 128))
            self.player_images.append(img)

        # 3. Disease/City Markers
        self.city_colors_imgs = {}
        files_map = {
            "Blue": ("images/azul.png", "images/centro_azul.png", (0, 100, 255)),
            "Yellow": ("images/amarillo.png", "images/centro_amarillo.png", (255, 255, 0)),
            "Black": ("images/negro.png", "images/centro_negro.png", (50, 50, 50)),
            "Red": ("images/rojo.png", "images/centro_rojo.png", (255, 0, 0))
        }
        
        for c_name, (norm_file, center_file, fallback_color) in files_map.items():
            # Standard
            self.city_colors_imgs[c_name] = load_image_or_create_fallback(norm_file, (30, 30), fallback_color)
            
            # Center
            center_img = load_image_or_create_fallback(center_file, (30, 30), fallback_color)
            self.city_colors_imgs[c_name + "_Center"] = center_img
        
        # 4. Track Markers
        # Updated per request: Track 309x38, Marker 70x70
        self.infection_track_img = load_image_or_create_fallback("images/infection_track_mark.png", (309, 38), (100, 100, 100))
        self.infection_marker_img = load_image_or_create_fallback("images/infection.png", (70, 70), (255, 50, 50))

        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_medium = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        
        self.colors = {
            "Blue": (0, 100, 255), "Yellow": (255, 255, 0),
            "Black": (50, 50, 50), "Red": (255, 0, 0),
            "White": (255, 255, 255), "UI_BG": (10, 10, 20, 200),
            "Text": (255, 255, 255)
        }

        self.city_coords = {
            "San Francisco": (100, 150), "Chicago": (210, 130), "Montreal": (300, 130),
            "New York": (350, 140), "Atlanta": (240, 190), "Washington": (330, 190),
            "London": (520, 110), "Madrid": (510, 200), "Paris": (580, 150),
            "Essen": (600, 100), "Milan": (630, 140), "St. Petersburg": (700, 80),
            "Los Angeles": (100, 230), "Mexico City": (180, 300), "Miami": (290, 280),
            "Bogota": (280, 370), "Lima": (260, 460), "Santiago": (270, 560),
            "Buenos Aires": (360, 540), "Sao Paulo": (400, 430), "Lagos": (580, 360),
            "Khartoum": (680, 340), "Kinshasa": (630, 440), "Johannesburg": (660, 530),
            "Algiers": (590, 230), "Istanbul": (680, 180), "Cairo": (670, 250),
            "Moscow": (750, 110), "Baghdad": (760, 210), "Tehran": (820, 170),
            "Riyadh": (780, 290), "Karachi": (860, 240), "Delhi": (920, 200),
            "Mumbai": (880, 310), "Chennai": (940, 370), "Kolkata": (1000, 220),
            "Bangkok": (1010, 300), "Jakarta": (1020, 410), "Ho Chi Minh": (1080, 340),
            "Hong Kong": (1060, 270), "Shanghai": (1050, 190), "Beijing": (1040, 120),
            "Seoul": (1120, 120), "Tokyo": (1180, 150), "Osaka": (1180, 210),
            "Taipei": (1130, 260), "Manila": (1150, 340), "Sydney": (1180, 510)
        }

        self.planned_actions: List[Tuple[str, Optional[str]]] = []
        self.buttons = self._create_buttons()
        self.active_modal: Optional[object] = None
        
        self.show_actions_menu = False
        self.actions_map = {
            "Mover": "move",
            "Curar": "cure",
            "Construir": "build",
            "Vuelo Directo": "direct_flight",
            "Vuelo Charter": "charter_flight",
            "Descubrir Cura": "discover_cure",
            "Compartir": "share",
            "Puente Aéreo": "shuttle"
        }
        self.actions_menu_rects = []
        self._init_action_menu_rects()
        
        # Log Scroll
        self.log_scroll_offset = 0

    def _create_buttons(self):
        buttons = {}
        buttons["actions_menu"] = {"rect": pygame.Rect(20, 620, 160, 40), "text": "Acciones"}
        buttons["clear"] = {"rect": pygame.Rect(20, 670, 100, 40), "text": "Borrar"}
        buttons["execute"] = {"rect": pygame.Rect(130, 670, 100, 40), "text": "Ejecutar"}
        buttons["view_others"] = {"rect": pygame.Rect(630, 640, 100, 40), "text": "Otros"}
        return buttons

    def _init_action_menu_rects(self):
        base_y = 620
        item_height = 30
        actions_list = list(self.actions_map.keys())
        total_height = len(actions_list) * item_height
        start_y = base_y - total_height
        
        for i, action_text in enumerate(actions_list):
            r = pygame.Rect(20, start_y + i * item_height, 160, item_height)
            self.actions_menu_rects.append({
                "rect": r, 
                "text": action_text, 
                "key": self.actions_map[action_text]
            })

    def run(self):
        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return "EXIT"
                
                # Log Scrolling
                if event.type == pygame.MOUSEWHEEL:
                    mx, my = pygame.mouse.get_pos()
                    # Check if over log
                    if 1000 <= mx <= 1270 and 610 <= my <= 790:
                         self.log_scroll_offset += event.y
                         self.log_scroll_offset = max(0, min(self.log_scroll_offset, len(self.game.log) - 9))

                if self.active_modal:
                    offset_x = self.screen_size[0] // 2 - self.active_modal.width // 2
                    offset_y = self.screen_size[1] // 2 - self.active_modal.height // 2
                    if hasattr(self.active_modal, "handle_event"):
                        if self.active_modal.handle_event(event, offset_x, offset_y): pass
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.game.game_over:
                        self.handle_click(event.pos)
                    if event.type == pygame.KEYDOWN and self.game.game_over:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            return "MENU"

            self.draw()
            pygame.display.flip()
            clock.tick(30)
        return "EXIT"

    def _get_virtual_state(self):
        """Returns (sim_location, sim_hand, sim_stations) based on planned actions."""
        p = self.game.players[self.game.current_player_index]
        sim_loc = p.location
        sim_hand = p.hand[:]
        sim_stations = self.game.research_stations[:]
        
        for act, param in self.planned_actions:
            act = act.lower()
            if act == "move":
                sim_loc = param # Simple move assumes valid
            elif act == "direct_flight":
                # Remove dest card
                for c in sim_hand:
                    if c.lower() == param.lower():
                        sim_hand.remove(c)
                        break
                sim_loc = param
            elif act == "charter_flight":
                # Remove origin card
                for c in sim_hand:
                    if c.lower() == sim_loc.lower():
                        sim_hand.remove(c)
                        break
                sim_loc = param
            elif act == "shuttle":
                sim_loc = param
            elif act == "build":
                for c in sim_hand:
                    if c.lower() == sim_loc.lower():
                        sim_hand.remove(c)
                        sim_stations.append(sim_loc)
                        break
            elif act == "event":
                 card_name = param["name"]
                 if card_name in sim_hand: sim_hand.remove(card_name)
                 kwargs = param.get("kwargs", {})
                 if card_name == "PUENTE_AEREO":
                     if kwargs.get("target_player_idx") == self.game.current_player_index:
                         sim_loc = kwargs.get("dest_city")
                 elif card_name == "SUBSIDIO_GUBERNAMENTAL":
                     t = kwargs.get("target_city")
                     if t: sim_stations.append(t)
            
        return sim_loc, sim_hand, sim_stations

    def handle_click(self, pos):
        if self.show_actions_menu:
            clicked_action = None
            for item in self.actions_menu_rects:
                if item["rect"].collidepoint(pos):
                    clicked_action = item["key"]
                    break
            self.show_actions_menu = False
            if clicked_action:
                self._trigger_action(clicked_action)
                return
            if self.buttons["actions_menu"]["rect"].collidepoint(pos):
                pass 
            else:
                return 

        # 1. Check Hand for Events (Update coord check due to line wrap)
        start_x = 280
        start_y = 640
        player = self.game.players[self.game.current_player_index]
        for i, card in enumerate(player.hand):
            # Calculate position same as draw_current_hand
            x_pos = start_x + (i % 4) * 80
            y_pos = start_y + (i // 4) * 50
            r = pygame.Rect(x_pos, y_pos, 75, 45)
            
            if r.collidepoint(pos):
                if card in EVENT_NAMES:
                    self._trigger_event(card)
                return

        # 2. Check City Clicks (Move)
        for city_name, city_pos in self.city_coords.items():
            if pygame.Rect(city_pos[0]-15, city_pos[1]-15, 30, 30).collidepoint(pos):
                # Count only standard actions
                std_actions = sum(1 for a in self.planned_actions if a[0] != "event")
                if std_actions < 4:
                    self.planned_actions.append(("move", city_name))
                return

        # 3. Check UI Buttons
        for name, btn in self.buttons.items():
            if btn["rect"].collidepoint(pos):
                if name == "actions_menu":
                    self.show_actions_menu = not self.show_actions_menu
                elif name == "execute":
                    self._handle_execute_turn()
                elif name == "clear":
                    self.planned_actions = []
                elif name == "view_others":
                    self.active_modal = PlayerHandsModal(self.game, self._on_modal_cancel)
                return

    def _handle_execute_turn(self):
        std_actions = sum(1 for a in self.planned_actions if a[0] != "event")
        if std_actions != 4:
            self.game.log_msg("Debes seleccionar exactamente 4 acciones (los eventos son libres).")
            return
        
        # Validate whole plan
        if not self.game.validate_turn_plan(self.game.current_player_index, self.planned_actions):
             self.game.log_msg(f"Error: La secuencia de acciones no es válida.")
             return
        
        # 1. Execute Actions
        if not self.game.execute_turn_actions(self.planned_actions):
             # Game Over triggered during actions
             self.planned_actions = []
             return

        self.planned_actions = []

        # 2. Draw Cards
        self.game.draw_phase_cards()
        if self.game.game_over: return
        
        # 3. Check Hand Limit
        if self.game.check_hand_limit():
            self.active_modal = DiscardModal(self.game, self._on_discard_confirm)
        else:
            self._finish_turn_sequence()

    def _on_discard_confirm(self, card_name):
        self.game.player_discard(card_name)
        # Check if still over limit
        if self.game.check_hand_limit():
             # Re-open/Keep open logic implied, just don't close or reset modal state
             pass
        else:
             self.active_modal = None
             self._finish_turn_sequence()

    def _finish_turn_sequence(self):
        self.game.end_turn_sequence()

    def _trigger_event(self, card_name):
        # Specific Modals for Events
        if card_name == "UNA_NOCHE_TRANQUILA":
            # Direct queue
            self._queue_event(card_name, {})
        
        elif card_name == "POBLACION_RESILIENTE":
            self.active_modal = ResilientModal(self.game, 
                lambda target: self._queue_event(card_name, {"target_card": target}), 
                self._on_modal_cancel)
                
        elif card_name == "SUBSIDIO_GUBERNAMENTAL":
            self.active_modal = CitySelectionModal("Seleccionar Ciudad para Estación (Subsidio)",
                [c for c in self.game.cities], self.game,
                lambda c: self._queue_event(card_name, {"target_city": c}),
                self._on_modal_cancel)
                
        elif card_name == "PUENTE_AEREO":
            self.active_modal = AirliftModal(self.game,
                lambda pid, dest: self._queue_event(card_name, {"target_player_idx": pid, "dest_city": dest}),
                self._on_modal_cancel)
                
        elif card_name == "PREDICCION":
            self.active_modal = ForecastModal(self.game,
                lambda order: self._queue_event(card_name, {"new_order": order}),
                self._on_modal_cancel)

    def _queue_event(self, card_name, kwargs):
        self.planned_actions.append(("event", {"name": card_name, "kwargs": kwargs}))
        self.active_modal = None

    def _trigger_action(self, action_key):
        # Use Virtual State to allow chaining moves
        sim_loc, sim_hand, sim_stations = self._get_virtual_state()
        
        if action_key == "share":
             self.active_modal = ShareKnowledgeModal(self.game, 
                lambda atype, msg: self._on_modal_share_confirm(msg), 
                self._on_modal_cancel,
                current_location=sim_loc,
                current_hand=sim_hand)
             return

        if action_key == "move":
            # Show neighbors of VIRTUAL location
            current = sim_loc
            neighbors = self.game.cities[current.lower()].neighbors
            self.active_modal = CitySelectionModal(f"Mover desde {current}", sorted(neighbors), self.game,
                lambda city: self._on_modal_confirm("move", city),
                self._on_modal_cancel)
            return

        if action_key == "direct_flight":
            # Valid destinations are cards in VIRTUAL hand
            valid_cities = []
            for card in sim_hand:
                if card.lower() in self.game.cities:
                    valid_cities.append(self.game.cities[card.lower()].name)
            valid_cities = sorted(valid_cities)
            
            if not valid_cities:
                self.game.log_msg("No tienes cartas para Vuelo Directo (en secuencia planificada).")
                return
            self.active_modal = CitySelectionModal(
                "Seleccionar Destino (Vuelo Directo)", valid_cities, self.game,
                callback_confirm=lambda city: self._on_modal_confirm("direct_flight", city),
                callback_cancel=self._on_modal_cancel
            )
            
        elif action_key == "charter_flight":
            # Need card of VIRTUAL location
            has_card = False
            for card in sim_hand:
                if card.lower() == sim_loc.lower():
                    has_card = True
                    break
                    
            if not has_card:
                self.game.log_msg(f"Necesitas la carta de {sim_loc} para Vuelo Charter.")
                return
            
            # Can go anywhere except current virtual loc
            all_cities = sorted([c.name for c in self.game.cities.values() if c.name != sim_loc])
            self.active_modal = CitySelectionModal(
                "Seleccionar Destino (Vuelo Charter)", all_cities, self.game,
                callback_confirm=lambda city: self._on_modal_confirm("charter_flight", city),
                callback_cancel=self._on_modal_cancel
            )
            
        elif action_key == "shuttle":
             if sim_loc not in sim_stations:
                 self.game.log_msg(f"{sim_loc} no tiene estación para Puente Aéreo.")
                 return
             valid = [s for s in sim_stations if s != sim_loc]
             if not valid:
                 self.game.log_msg("No hay otras estaciones construidas.")
                 return
             self.active_modal = CitySelectionModal(
                "Seleccionar Destino (Puente Aéreo)", sorted(valid), self.game,
                callback_confirm=lambda city: self._on_modal_confirm("shuttle", city),
                callback_cancel=self._on_modal_cancel
            )
            
        else:
            std_actions = sum(1 for a in self.planned_actions if a[0] != "event")
            if std_actions < 4:
                self.planned_actions.append((action_key, None))

    def _on_modal_confirm(self, action_type, city_name):
        std_actions = sum(1 for a in self.planned_actions if a[0] != "event")
        if std_actions < 4:
            self.planned_actions.append((action_type, city_name))
        self.active_modal = None

    def _on_modal_share_confirm(self, log_msg):
        self.game.log_msg(f"[ACCIÓN COMPARTIR] {log_msg}")
        self.active_modal = None

    def _on_modal_cancel(self):
        self.active_modal = None

    def draw(self):
        self.screen.blit(self.map_image, (0, 0))
        self.draw_connections()
        self.draw_cities()
        self.draw_players()
        self.draw_ui_panels()
        self.draw_infection_track()
        self.draw_buttons()
        self.draw_current_hand()
        self.draw_planned_actions()
        self.draw_log()
        if self.show_actions_menu:
            self.draw_action_dropdown()
        self.draw_game_state()
        if self.game.game_over:
            self.draw_game_over()
        if self.active_modal:
            dim_surf = pygame.Surface(self.screen_size)
            dim_surf.set_alpha(150)
            dim_surf.fill((0, 0, 0))
            self.screen.blit(dim_surf, (0, 0))
            if hasattr(self.active_modal, 'draw'):
                self.active_modal.draw(self.screen, (self.screen_size[0]//2, self.screen_size[1]//2))

    def draw_connections(self):
        for city_name, city_pos in self.city_coords.items():
            city_obj = self.game.cities.get(city_name.lower())
            if not city_obj: continue
            for neighbor_name in city_obj.neighbors:
                neighbor_pos = self.city_coords.get(neighbor_name)
                if neighbor_pos:
                    is_pacific_edge = (
                        (city_name == "San Francisco" and neighbor_name in ["Tokyo", "Manila"]) or
                        (city_name == "Los Angeles" and neighbor_name == "Sydney") or
                        (city_name in ["Tokyo", "Manila"] and neighbor_name == "San Francisco") or
                        (city_name == "Sydney" and neighbor_name == "Los Angeles")
                    )
                    if is_pacific_edge:
                        if city_pos[0] < self.screen_size[0] / 2: 
                            pygame.draw.line(self.screen, self.colors["White"], city_pos, (0, neighbor_pos[1]), 2)
                        else:
                            pygame.draw.line(self.screen, self.colors["White"], city_pos, (self.screen_size[0], neighbor_pos[1]), 2)
                    else:
                        pygame.draw.line(self.screen, self.colors["White"], city_pos, neighbor_pos, 1)

    def draw_cities(self):
        for city_name, city_pos in self.city_coords.items():
            city_obj = self.game.cities.get(city_name.lower())
            if not city_obj: continue
            
            # Determine image key
            base_key = city_obj.color
            key = base_key
            if city_name in self.game.research_stations:
                key = base_key + "_Center"
            
            img = self.city_colors_imgs.get(key)
            
            # Fallback if center image missing but station exists: use base image
            if not img and "_Center" in key:
                 img = self.city_colors_imgs.get(base_key)
            
            if img:
                self.screen.blit(img, (city_pos[0]-15, city_pos[1]-15))
                # Only draw white rect if we fell back to normal image for a station
                if city_name in self.game.research_stations and key != (base_key + "_Center"):
                     pygame.draw.rect(self.screen, self.colors["White"], (city_pos[0]-6, city_pos[1]-6, 12, 12))
            else:
                 # Fallback to circle
                 pygame.draw.circle(self.screen, self.colors[city_obj.color], city_pos, 10)
                 if city_name in self.game.research_stations:
                     pygame.draw.rect(self.screen, self.colors["White"], (city_pos[0]-6, city_pos[1]-6, 12, 12))

            if city_obj.infections > 0:
                color = self.colors[city_obj.color]
                for i in range(city_obj.infections):
                    pygame.draw.rect(self.screen, color, (city_pos[0] + 10 + i * 12, city_pos[1] - 10, 10, 10))
                count_text = self.font_medium.render(str(city_obj.infections), True, self.colors["White"])
                self.screen.blit(count_text, (city_pos[0] + 12, city_pos[1] - 30))
            
            text = self.font_small.render(city_name, True, self.colors["Text"])
            self.screen.blit(text, city_pos)

    def draw_players(self):
        for i, player in enumerate(self.game.players):
            pos = self.city_coords.get(player.location)
            if pos:
                img = self.player_images[i] if i < len(self.player_images) else None
                if img:
                    draw_pos = (pos[0] - 8 - i*5, pos[1] - 30 + i*2)
                    self.screen.blit(img, draw_pos)
                else:
                    pygame.draw.circle(self.screen, (200, 200, 200), (pos[0] - 10 - i*5, pos[1] + 10), 8)
                p_text = self.font_small.render(f"P{i+1}", True, self.colors["Black"])
                self.screen.blit(p_text, (pos[0] - 15 - i*5, pos[1] + 5))

    def draw_ui_panels(self):
        s = pygame.Surface((self.screen_size[0], 200))
        s.set_alpha(200)
        s.fill(self.colors["UI_BG"])
        self.screen.blit(s, (0, self.screen_size[1] - 200))
        
    def draw_infection_track(self):
        base_x = self.screen_size[0] - 320
        base_y = 20
        # --- Infection Track Logic: 309x38 ---
        if self.infection_track_img:
            self.screen.blit(self.infection_track_img, (base_x, base_y))
            idx = self.game.infection_rate_index
            if idx >= 7: idx = 6
            
            # 7 steps across 309 pixels width
            step_width = 309 / 7
            marker_x = base_x + (idx * step_width)
            marker_y = base_y
            
            if self.infection_marker_img:
                # Center 70px marker on step slot
                # (step_width / 2) - (marker_width / 2) -> centers relative to step
                marker_centered_x = marker_x + (step_width / 2) - (70 / 2)
                
                # Center vertically relative to 38px height track
                # (track_height / 2) - (marker_height / 2)
                marker_centered_y = marker_y + (38 / 2) - (70 / 2)
                
                self.screen.blit(self.infection_marker_img, (marker_centered_x, marker_centered_y))
        else:
             rate_text = f"Tasa Infección: {self.game.infection_rate_list[self.game.infection_rate_index]}"
             self.screen.blit(self.font_medium.render(rate_text, True, self.colors["Yellow"]), (self.screen_size[0] - 250, 20))

    def draw_action_dropdown(self):
        for item in self.actions_menu_rects:
            pygame.draw.rect(self.screen, (50, 50, 70), item["rect"])
            pygame.draw.rect(self.screen, (150, 150, 150), item["rect"], 1)
            mouse_pos = pygame.mouse.get_pos()
            if item["rect"].collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, (80, 80, 100), item["rect"])
                pygame.draw.rect(self.screen, (200, 200, 200), item["rect"], 1)
            text_surf = self.font_small.render(item["text"], True, self.colors["White"])
            self.screen.blit(text_surf, (item["rect"].x + 10, item["rect"].y + 5))

    def draw_current_hand(self):
        if not self.game.players: return
        player = self.game.players[self.game.current_player_index]
        start_x = 280
        start_y = 640
        title = self.font_medium.render(f"Mano ({player.name}):", True, self.colors["Text"])
        self.screen.blit(title, (start_x, 615))

        for i, card in enumerate(player.hand):
            # --- Hand Wrap Logic (4 cards per row) ---
            col = i % 4
            row = i // 4
            x_pos = start_x + col * 80
            y_pos = start_y + row * 50
            
            card_rect = pygame.Rect(x_pos, y_pos, 75, 45)

            if card in EVENT_NAMES:
                color = (50, 205, 50) # Lime Green
                display_text = EVENT_DISPLAY_NAMES[card]
                if len(display_text) > 12:
                    display_text = display_text[:10] + "..."
            else:
                try:
                    color = self.colors[self.game.cities[card.lower()].color]
                except KeyError:
                    color = self.colors["White"]
                display_text = card[:12]
            
            pygame.draw.rect(self.screen, color, card_rect)
            pygame.draw.rect(self.screen, (0,0,0), card_rect, 1)
            
            txt_col = self.colors["Black"]
            if color == self.colors["Black"]: txt_col = (255, 255, 255)
            
            card_text = self.font_small.render(display_text, True, txt_col)
            self.screen.blit(card_text, (card_rect.x + 3, card_rect.y + 15))

    def draw_planned_actions(self):
        start_x = 780
        title = self.font_medium.render("Acciones Planeadas:", True, self.colors["Text"])
        self.screen.blit(title, (start_x, 615))
        for i, (action, param) in enumerate(self.planned_actions):
            text = ""
            if action == "event":
                text = f"{i+1}. Evento: {EVENT_DISPLAY_NAMES.get(param['name'], param['name'])}"
            else:
                text = f"{i+1}. {action} {param or ''}"
            
            action_text = self.font_small.render(text, True, self.colors["Text"])
            self.screen.blit(action_text, (start_x, 645 + i * 20))
    
    def draw_buttons(self):
        for name, btn in self.buttons.items():
            color = self.colors["Blue"]
            if name == "actions_menu" and self.show_actions_menu:
                color = (100, 100, 150)
            if name == "execute":
                std_actions = sum(1 for a in self.planned_actions if a[0] != "event")
                if std_actions != 4:
                     color = (100, 100, 100)
            pygame.draw.rect(self.screen, color, btn["rect"])
            pygame.draw.rect(self.screen, (200, 200, 200), btn["rect"], 1)
            text = self.font_medium.render(btn["text"], True, self.colors["White"])
            self.screen.blit(text, (btn["rect"].x + 10, btn["rect"].y + 10))

    def draw_game_state(self):
        outbreak_text = f"Brotes: {self.game.outbreaks}/8"
        self.screen.blit(self.font_medium.render(outbreak_text, True, self.colors["Red"]), (20, 20))
        for i, (color, discovered) in enumerate(self.game.cures_discovered.items()):
            pos = (200 + i * 100, 20)
            pygame.draw.rect(self.screen, self.colors[color], (pos[0], pos[1], 80, 30), border_radius=5)
            if discovered:
                status = "CURADA" if not self.game.eradicated[color] else "ERRADICADA"
                cure_text = self.font_small.render(status, True, self.colors["Black"])
                self.screen.blit(cure_text, (pos[0] + 10, pos[1] + 8))

    def draw_log(self):
        log_width = 270
        log_height = 180
        start_x = 1000
        start_y = 610
        log_surface = pygame.Surface((log_width, log_height))
        log_surface.set_alpha(180)
        log_surface.fill(self.colors["UI_BG"])
        self.screen.blit(log_surface, (start_x, start_y))
        
        # Calculate view
        visible_lines = 9
        total_lines = len(self.game.log)
        
        # Determine start index based on scroll offset. 
        # offset 0 = show latest 9 lines (end of list)
        # offset N = go back N lines
        end_idx = total_lines - self.log_scroll_offset
        start_idx = max(0, end_idx - visible_lines)
        
        msgs_to_show = self.game.log[start_idx:end_idx]
        
        for i, msg in enumerate(msgs_to_show):
            log_text = self.font_small.render(msg, True, self.colors["Text"])
            self.screen.blit(log_text, (start_x + 10, start_y + 10 + i * 18))

    def draw_game_over(self):
        s = pygame.Surface(self.screen_size)
        s.set_alpha(200)
        s.fill(self.colors["Black"])
        self.screen.blit(s, (0, 0))
        text = self.font_large.render("FIN DEL JUEGO", True, self.colors["Red"])
        reason = self.font_medium.render(self.game.defeat_reason or "Fin de la partida", True, self.colors["White"])
        esc_msg = self.font_small.render("Presiona ESC para volver al menú", True, (200, 200, 200))
        self.screen.blit(text, (self.screen_size[0]/2 - text.get_width()/2, self.screen_size[1]/2 - 50))
        self.screen.blit(reason, (self.screen_size[0]/2 - reason.get_width()/2, self.screen_size[1]/2))
        self.screen.blit(esc_msg, (self.screen_size[0]/2 - esc_msg.get_width()/2, self.screen_size[1]/2 + 50))