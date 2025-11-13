import pygame
import random
from typing import Dict, List, Optional, Tuple

# =============================================================================
# PARTE 1: LÓGICA DEL JUEGO (NÚCLEO v0.4 CON LOG INTEGRADO)
# =============================================================================

class City:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.infections = 0
        self.neighbors: List[str] = []

    def add_neighbor(self, other_city_name: str):
        if other_city_name not in self.neighbors:
            self.neighbors.append(other_city_name)

class Player:
    def __init__(self, name: str, start_city: str):
        self.name = name
        self.location = start_city
        self.hand: List[str] = []

    def move_to(self, city_name: str):
        self.location = city_name

class InfectionDeck:
    def __init__(self, cities: List[str]):
        self.deck: List[str] = list(cities)
        random.shuffle(self.deck)
        self.discard_pile: List[str] = []

    def draw_top(self) -> str:
        if not self.deck: raise IndexError("InfectionDeck vacío")
        return self.deck.pop(0)

    def draw_bottom(self) -> str:
        if not self.deck: raise IndexError("InfectionDeck vacío")
        return self.deck.pop()

    def discard(self, card: str):
        self.discard_pile.append(card)

    def shuffle_discard_onto_deck_top(self):
        if not self.discard_pile: return
        random.shuffle(self.discard_pile)
        self.deck = self.discard_pile + self.deck
        self.discard_pile = []

class PlayerDeck:
    def __init__(self, cities: List[str], n_epidemics: int = 4, n_events: int = 5, seed: Optional[int] = None):
        if seed is not None: random.seed(seed)
        base = list(cities)
        for i in range(1, n_events + 1):
            base.append(f"EVENT_{i}")
        random.shuffle(base)
        
        piles: List[List[str]] = []
        n = n_epidemics
        pile_size = len(base) // n
        for i in range(n):
            pile = base[i*pile_size:(i+1)*pile_size]
            pile.append("EPIDEMIC")
            random.shuffle(pile)
            piles.append(pile)
        
        self.deck: List[str] = [card for pile in piles for card in pile]
        self.discard_pile: List[str] = []

    def draw_card(self) -> str:
        if not self.deck: raise IndexError("PlayerDeck vacío")
        return self.deck.pop(0)

    def discard(self, card: str):
        self.discard_pile.append(card)

class Game:
    MAX_RESEARCH_STATIONS = 6
    PLAYER_HAND_LIMIT = 7

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

        # Log de mensajes para la GUI
        self.log: List[str] = []

        # Mapa y jugadores
        self.cities: Dict[str, City] = {}
        self.players: List[Player] = []
        self.current_player_index = 0

        # Contadores y estados
        self.infection_rate_list = [2, 2, 2, 3, 3, 4, 4]
        self.infection_rate_index = 0
        self.outbreaks = 0
        self.turn = 1

        self.game_over = False
        self.defeat_reason: Optional[str] = None

        # Investigación y curas
        self.research_stations: List[str] = []  # nombres de ciudades con estación
        self.cures_discovered: Dict[str, bool] = {"Blue": False, "Yellow": False, "Black": False, "Red": False}
        self.eradicated: Dict[str, bool] = {"Blue": False, "Yellow": False, "Black": False, "Red": False}

        # Setup mapa y mazos
        self._setup_full_map()
        city_names = [c.name for c in self.cities.values()]
        self.infection_deck = InfectionDeck(city_names)
        self.player_deck = PlayerDeck(city_names, seed=seed)
        # reparto inicial y estado
        self._initial_infections()

    # ---------------------------
    # Sistema de log
    # ---------------------------
    def log_msg(self, text: str):
        """Envía un mensaje tanto a consola como al log interno."""
        print(text)
        self.log.append(text)
        # Limitar tamaño del log para la GUI
        if len(self.log) > 200:
            self.log.pop(0)

    # ---------------------------
    # Mapa
    # ---------------------------
    def _add_city(self, name: str, color: str):
        self.cities[name.lower()] = City(name, color)

    def _connect(self, a: str, b: str):
        a_key, b_key = a.lower(), b.lower()
        if a_key not in self.cities or b_key not in self.cities:
            raise ValueError(f"Intentando conectar ciudades desconocidas: {a} - {b}")
        self.cities[a_key].add_neighbor(self.cities[b_key].name)
        self.cities[b_key].add_neighbor(self.cities[a_key].name)

    def _setup_full_map(self):
        blue = ["San Francisco","Chicago","Atlanta","Montreal","New York","Washington","London","Madrid","Paris","Essen","Milan","St. Petersburg"]
        yellow = ["Los Angeles","Mexico City","Miami","Bogota","Lima","Santiago","Buenos Aires","Sao Paulo","Lagos","Khartoum","Kinshasa","Johannesburg"]
        black = ["Algiers","Istanbul","Moscow","Cairo","Baghdad","Tehran","Karachi","Riyadh","Delhi","Mumbai","Chennai","Kolkata"]
        red = ["Bangkok","Jakarta","Ho Chi Minh City","Hong Kong","Shanghai","Beijing","Seoul","Tokyo","Osaka","Taipei","Manila","Sydney"]
        for name in blue: self._add_city(name, "Blue")
        for name in yellow: self._add_city(name, "Yellow")
        for name in black: self._add_city(name, "Black")
        for name in red: self._add_city(name, "Red")
        connections = [
            ("San Francisco", ["Tokyo", "Manila", "Los Angeles", "Chicago"]),("Chicago", ["San Francisco", "Los Angeles", "Mexico City", "Atlanta", "Montreal"]),
            ("Atlanta", ["Chicago", "Washington", "Miami"]),("Montreal", ["Chicago", "New York", "Washington"]),
            ("New York", ["Montreal", "Washington", "London", "Madrid"]),("Washington", ["Atlanta", "New York", "Montreal", "Miami"]),
            ("London", ["New York", "Madrid", "Paris", "Essen"]),("Madrid", ["New York", "London", "Paris", "Algiers", "Sao Paulo"]),
            ("Paris", ["London", "Essen", "Milan", "Algiers", "Madrid"]),("Essen", ["London", "Paris", "Milan", "St. Petersburg"]),
            ("Milan", ["Essen", "Paris", "Istanbul"]),("St. Petersburg", ["Essen", "Istanbul", "Moscow"]),
            ("Los Angeles", ["San Francisco", "Chicago", "Mexico City", "Sydney"]),("Mexico City", ["Los Angeles", "Chicago", "Miami", "Bogota", "Lima"]),
            ("Miami", ["Atlanta", "Washington", "Mexico City", "Bogota"]),("Bogota", ["Mexico City", "Miami", "Lima", "Buenos Aires", "Sao Paulo"]),
            ("Lima", ["Mexico City", "Bogota", "Santiago"]),("Santiago", ["Lima"]),("Buenos Aires", ["Bogota", "Sao Paulo"]),
            ("Sao Paulo", ["Buenos Aires", "Bogota", "Madrid", "Lagos"]),("Lagos", ["Sao Paulo", "Khartoum", "Kinshasa"]),
            ("Khartoum", ["Lagos", "Kinshasa", "Johannesburg", "Cairo"]),("Kinshasa", ["Lagos", "Khartoum", "Johannesburg"]),
            ("Johannesburg", ["Kinshasa", "Khartoum"]),("Algiers", ["Madrid", "Paris", "Istanbul", "Cairo"]),
            ("Istanbul", ["Milan", "St. Petersburg", "Moscow", "Baghdad", "Cairo", "Algiers"]),("Moscow", ["St. Petersburg", "Istanbul", "Tehran"]),
            ("Cairo", ["Algiers", "Istanbul", "Baghdad", "Khartoum", "Riyadh"]),("Baghdad", ["Istanbul", "Tehran", "Karachi", "Riyadh", "Cairo"]),
            ("Tehran", ["Moscow", "Baghdad", "Karachi", "Delhi"]),("Karachi", ["Tehran", "Baghdad", "Riyadh", "Mumbai", "Delhi"]),
            ("Riyadh", ["Cairo", "Baghdad", "Karachi"]),("Delhi", ["Tehran", "Karachi", "Mumbai", "Chennai", "Kolkata"]),
            ("Mumbai", ["Karachi", "Delhi", "Chennai"]),("Chennai", ["Mumbai", "Delhi", "Kolkata", "Bangkok", "Jakarta"]),
            ("Kolkata", ["Delhi", "Chennai", "Bangkok", "Hong Kong"]),("Bangkok", ["Kolkata", "Chennai", "Jakarta", "Ho Chi Minh City", "Hong Kong"]),
            ("Jakarta", ["Chennai", "Bangkok", "Ho Chi Minh City", "Sydney"]),("Ho Chi Minh City", ["Jakarta", "Bangkok", "Hong Kong", "Manila"]),
            ("Hong Kong", ["Kolkata", "Bangkok", "Ho Chi Minh City", "Shanghai", "Taipei", "Manila"]),("Shanghai", ["Beijing", "Seoul", "Tokyo", "Hong Kong", "Taipei"]),
            ("Beijing", ["Shanghai", "Seoul"]),("Seoul", ["Beijing", "Shanghai", "Tokyo"]),
            ("Tokyo", ["Seoul", "Shanghai", "Osaka", "San Francisco"]),("Osaka", ["Tokyo", "Taipei"]),
            ("Taipei", ["Osaka", "Shanghai", "Hong Kong", "Manila"]),("Manila", ["Taipei", "Hong Kong", "Ho Chi Minh City", "Sydney", "San Francisco"]),
            ("Sydney", ["Jakarta", "Manila", "Los Angeles"])
        ]
        for city_name, neighs in connections:
            for nb in neighs:
                try:
                    self._connect(city_name, nb)
                except ValueError:
                    #self.log_msg(f"Advertencia al conectar: {e}")
                    pass

    def _initial_infections(self):
        self.log_msg("\n--- Infecciones Iniciales ---")
        for i in range(3):  # 3 ciudades con 3, 2, 1 cubos
            city_card = self.infection_deck.draw_top()
            self.infect_city(city_card, 3 - i, source="initial")
            self.infection_deck.discard(city_card)
        for i in range(3):  # 3 ciudades con 1 cubo
            city_card = self.infection_deck.draw_top()
            self.infect_city(city_card, 1, source="initial")
            self.infection_deck.discard(city_card)
        self.log_msg("-----------------------------\n")

    def _outbreak_chain(self, city_key: str, visited: set):
        if city_key in visited:
            return
        visited.add(city_key)
        city = self.cities[city_key]
        self.outbreaks += 1
        self.log_msg(f"[BROTE] ¡{city.name} estalla! ({self.outbreaks}/8)")
        if self.outbreaks >= 8:
            self.game_over = True
            self.defeat_reason = "Límite de brotes alcanzado"
            self.log_msg(f"[DERROTA] {self.defeat_reason}")
            return

        for nb_name in city.neighbors:
            nb_key = nb_name.lower()
            nb_city = self.cities[nb_key]
            # No infectar si la enfermedad está erradicada
            if self.eradicated.get(nb_city.color, False):
                continue
            
            if nb_city.infections < 3:
                nb_city.infections += 1
                self.log_msg(f"  [BROTE->INFECT] {nb_city.name} recibe 1 cubo (ahora {nb_city.infections})")
            else:
                if nb_key not in visited:
                    self.log_msg(f"  [BROTE->CADENA] {nb_city.name} también estalla.")
                    self._outbreak_chain(nb_key, visited)

    def infect_city(self, city_name: str, cubes: int = 1, source: str = "generic"):
        if self.game_over: return
        key = city_name.lower()
        if key not in self.cities: return
        
        city = self.cities[key]
        color = city.color

        if self.eradicated.get(color, False):
            self.log_msg(f"[INFECT] {city.name}: enfermedad {color} erradicada, no se coloca cubo.")
            return

        self.log_msg(f"[INFECT] {city.name} (fuente: {source})")
        if city.infections + cubes <= 3:
            city.infections += cubes
            self.log_msg(f"  -> {city.name} ahora tiene {city.infections} cubos.")
        else:
            self.log_msg(f"  -> {city.name} ya tiene {city.infections}, añadir {cubes} causa un brote.")
            remaining_cubes = cubes
            while city.infections < 3 and remaining_cubes > 0:
                city.infections += 1
                remaining_cubes -= 1
            
            self._outbreak_chain(key, visited=set())
            if self.game_over: return

    def _handle_epidemic(self):
        self.log_msg("[EPIDEMIA] ¡Se activó una EPIDEMIA!")
        if self.infection_rate_index < len(self.infection_rate_list) - 1:
            self.infection_rate_index += 1
        self.log_msg(f"  [EPIDEMIA] El ritmo de infección aumenta a {self.infection_rate_list[self.infection_rate_index]}.")

        try:
            bottom_card = self.infection_deck.draw_bottom()
        except IndexError:
            self.game_over = True
            self.defeat_reason = "Mazo de infección agotado en epidemia"
            self.log_msg(f"[DERROTA] {self.defeat_reason}")
            return
        
        self.log_msg(f"  [EPIDEMIA] Carta inferior robada: {bottom_card} -> infectar con 3 cubos.")
        self.infect_city(bottom_card, cubes=3, source="epidemic")
        self.infection_deck.discard(bottom_card)
        if self.game_over: return

        self.infection_deck.shuffle_discard_onto_deck_top()

    def add_player(self, player_name: str, start_city: str = "Atlanta"):
        key = start_city.lower()
        if key not in self.cities: raise ValueError(f"Ciudad de inicio desconocida: {start_city}")
        
        # Reparto inicial basado en nº jugadores
        cards_to_deal = {1: 4, 2: 4, 3: 3, 4: 2}[min(4, len(self.players) + 1)]

        p = Player(player_name, self.cities[key].name)
        self.players.append(p)
        
        self.log_msg(f"Añadiendo jugador {p.name} en {self.cities[key].name}. Repartiendo {cards_to_deal} cartas...")
        try:
            for _ in range(cards_to_deal):
                card = self.player_deck.draw_card()
                if card == "EPIDEMIC":  # No se pueden robar en el setup
                    self.player_deck.deck.append(card)
                    random.shuffle(self.player_deck.deck)
                    card = self.player_deck.draw_card()
                p.hand.append(card)
        except IndexError:
            self.game_over = True
            self.defeat_reason = "Mazo de jugador agotado durante el reparto inicial"
            self.log_msg(f"[DERROTA] {self.defeat_reason}")
        return p

    def _get_city(self, city_name: str) -> City:
        key = city_name.lower()
        if key not in self.cities: raise ValueError(f"Ciudad desconocida: {city_name}")
        return self.cities[key]

    def share_knowledge(self, giver_index: int, receiver_index: int) -> bool:
        if self.game_over: return False
        giver, receiver = self.players[giver_index], self.players[receiver_index]
        
        if giver.location != receiver.location:
            self.log_msg("[ACCIÓN] Ambos jugadores deben estar en la misma ciudad.")
            return False
        
        city_name = giver.location
        if city_name not in giver.hand:
            self.log_msg(f"[ACCIÓN] {giver.name} no tiene la carta de {city_name}.")
            return False
        
        if len(receiver.hand) >= Game.PLAYER_HAND_LIMIT:
            self.log_msg(f"[ACCIÓN] {receiver.name} tiene la mano llena. No puede recibir cartas.")
            return False
        
        giver.hand.remove(city_name)
        receiver.hand.append(city_name)
        self.log_msg(f"[ACCIÓN] {giver.name} entregó {city_name} a {receiver.name}.")
        return True

    def shuttle(self, player_index: int, dest_city: str) -> bool:
        if self.game_over: return False
        player = self.players[player_index]
        if player.location not in self.research_stations:
            self.log_msg("[ACCIÓN] Debes estar en una estación para usar este vuelo.")
            return False
        if dest_city not in self.research_stations:
            self.log_msg("[ACCIÓN] El destino debe tener una estación.")
            return False
        
        origin = player.location
        player.move_to(dest_city)
        self.log_msg(f"[ACCIÓN] {player.name} voló de {origin} a {dest_city}.")
        return True

    def _check_and_set_eradication(self, color: str):
        if not self.cures_discovered.get(color, False) or self.eradicated.get(color, False):
            return
        
        is_eradicated = all(c.infections == 0 for c in self.cities.values() if c.color == color)
        if is_eradicated:
            self.eradicated[color] = True
            self.log_msg(f"[ERRADICADA] ¡La enfermedad {color} ha sido erradicada del tablero!")

    def _player_draw_card_to_hand(self, player: Player) -> bool:
        try:
            card = self.player_deck.draw_card()
        except IndexError:
            self.game_over = True
            self.defeat_reason = "Sin cartas en el mazo de jugador"
            self.log_msg(f"[DERROTA] {self.defeat_reason}")
            return False

        if card.startswith("EVENT"):
            self.log_msg(f"[ROBO] {player.name} robó una carta de Evento: {card}.")
            player.hand.append(card)
        elif card == "EPIDEMIC":
            self.player_deck.discard(card)
            self._handle_epidemic()
            if self.game_over: return False
        else:
            self.log_msg(f"[ROBO] {player.name} robó: {card}.")
            player.hand.append(card)

        # Descarte interactivo si se supera el límite de mano (modo consola)
        while len(player.hand) > Game.PLAYER_HAND_LIMIT:
            self.log_msg(f"¡Límite de mano excedido! ({len(player.hand)}/{Game.PLAYER_HAND_LIMIT})")
            for i, h_card in enumerate(player.hand, 1):
                self.log_msg(f"  {i}. {h_card}")
            try:
                choice = input(f"{player.name}, elige una carta para descartar (1-{len(player.hand)}): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(player.hand):
                    discarded = player.hand.pop(idx)
                    self.player_deck.discard(discarded)
                    self.log_msg(f"  -> Descartaste {discarded}.")
                else:
                    self.log_msg("Índice inválido.")
            except (ValueError, IndexError):
                self.log_msg("Entrada inválida.")
        return True

    def infection_phase(self):
        if self.game_over: return
        rate = self.infection_rate_list[self.infection_rate_index]
        self.log_msg(f"\n--- Fase de Infección (Robando {rate} cartas) ---")
        for _ in range(rate):
            try:
                card = self.infection_deck.draw_top()
            except IndexError:
                self.game_over = True
                self.defeat_reason = "Mazo de infección agotado"
                self.log_msg(f"[DERROTA] {self.defeat_reason}")
                return
            
            self.infect_city(card, cubes=1, source="infection_deck")
            self.infection_deck.discard(card)
            if self.game_over: return

    def run_turn(self, actions: List[Tuple[str, Optional[str]]], player_index: Optional[int] = None):
        if self.game_over: return
        
        if player_index is None:
            player_index = self.current_player_index

        player = self.players[player_index]
        self.log_msg(f"\n--- Ejecutando turno de {player.name} ---")
        actions_allowed = 4
        used = 0

        for i, act in enumerate(actions, 1):
            if used >= actions_allowed:
                break
            cmd, param = act[0].lower(), act[1]
            self.log_msg(f"Acción {i}: {cmd} {param or ''}")
            
            ok = self.perform_action((cmd, param), player_index)

            if ok:
                used += 1
            if self.game_over:
                return

        self.log_msg(f"\n--- Fase de Robo ({player.name}) ---")
        if not self._player_draw_card_to_hand(player): return
        if not self._player_draw_card_to_hand(player): return

        self.infection_phase()
        if self.game_over: return

        for color in ["Blue", "Yellow", "Black", "Red"]:
            self._check_and_set_eradication(color)

        if all(self.cures_discovered.values()):
            self.game_over = True
            self.log_msg("[VICTORIA] ¡Se descubrieron las 4 curas! ¡Habéis ganado!")
            return

        self.turn += 1
        if len(self.players) > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def perform_action(self, action: Tuple[str, Optional[str]], player_index: int = 0) -> bool:
        if self.game_over: return False
        player = self.players[player_index]
        act, param = action[0].lower(), action[1]

        if act == "move":
            try:
                dest = self._get_city(param)
                src = self._get_city(player.location)
                if dest.name in src.neighbors:
                    player.move_to(dest.name)
                    self.log_msg(f"[ACCIÓN] {player.name} se movió de {src.name} a {dest.name}.")
                    return True
                self.log_msg(f"[ACCIÓN] Movimiento inválido: {src.name} no está conectado con {dest.name}.")
                return False
            except (ValueError, TypeError):
                self.log_msg(f"[ACCIÓN] Ciudad destino inválida: {param}")
                return False

        elif act in ("cure", "treat"):
            city = self._get_city(player.location)
            if city.infections == 0:
                self.log_msg(f"[ACCIÓN] No hay infecciones que tratar en {city.name}.")
                return False
            
            color = city.color
            remove_amount = 3 if self.cures_discovered.get(color, False) else 1
            removed = min(city.infections, remove_amount)
            city.infections -= removed
            self.log_msg(f"[ACCIÓN] {player.name} trató {city.name}, quitando {removed} cubos (quedan {city.infections}).")
            self._check_and_set_eradication(color)
            return True

        elif act == "build":
            city_name = player.location
            if city_name in self.research_stations:
                self.log_msg(f"[ACCIÓN] Ya existe una estación en {city_name}.")
                return False
            if city_name not in player.hand:
                self.log_msg(f"[ACCIÓN] Necesitas la carta de {city_name} para construir.")
                return False
            if len(self.research_stations) >= Game.MAX_RESEARCH_STATIONS:
                self.log_msg(f"[ACCIÓN] Límite de estaciones alcanzado.")
                return False
            
            self.research_stations.append(city_name)
            player.hand.remove(city_name)
            self.player_deck.discard(city_name)
            self.log_msg(f"[ACCIÓN] {player.name} construyó una Estación de Investigación en {city_name}.")
            return True

        elif act == "discover_cure":
            city = self._get_city(player.location)
            if city.name not in self.research_stations:
                self.log_msg("[ACCIÓN] Debes estar en una estación para descubrir una cura.")
                return False
            
            color_counts = {"Blue": [], "Yellow": [], "Black": [], "Red": []}
            for card in player.hand:
                if card.lower() in self.cities:
                    card_color = self.cities[card.lower()].color
                    color_counts[card_color].append(card)

            CARDS_NEEDED = 5
            for col, cards in color_counts.items():
                if len(cards) >= CARDS_NEEDED and not self.cures_discovered[col]:
                    cards_to_discard = cards[:CARDS_NEEDED]
                    for c in cards_to_discard:
                        player.hand.remove(c)
                        self.player_deck.discard(c)
                    
                    self.cures_discovered[col] = True
                    self.log_msg(f"[CURA DESCUBIERTA] ¡Se ha descubierto la cura para la enfermedad {col}!")
                    self._check_and_set_eradication(col)
                    return True
            self.log_msg("[ACCIÓN] No tienes 5 cartas del mismo color para descubrir una cura.")
            return False

        elif act == "share":
            try:
                recv_idx = next(i for i, p in enumerate(self.players) if p.name.lower() == str(param).lower())
                return self.share_knowledge(player_index, recv_idx)
            except (StopIteration, TypeError):
                self.log_msg(f"[ACCIÓN] Jugador receptor '{param}' no encontrado.")
                return False

        elif act == "shuttle":
            try:
                self._get_city(param)  # Validar que la ciudad existe
                return self.shuttle(player_index, param)
            except (ValueError, TypeError):
                self.log_msg(f"[ACCIÓN] Ciudad destino inválida: {param}")
                return False

        elif act == "skip":
            self.log_msg(f"[ACCIÓN] {player.name} salta una acción.")
            return True

        else:
            self.log_msg(f"[ACCIÓN] Acción desconocida: {act}")
            return False

    def show_status(self):  # Método de diagnóstico
        self.log_msg("\n=== Estado del juego (Diagnóstico) ===")
        self.log_msg(f"Turno: {self.turn}, Jugador actual: {self.players[self.current_player_index].name}")
        self.log_msg(f"Infection rate: {self.infection_rate_list[self.infection_rate_index]} (Índice: {self.infection_rate_index})")
        self.log_msg(f"Brotes: {self.outbreaks}, Estaciones: {len(self.research_stations)}")
        self.log_msg(f"Curas: {self.cures_discovered}, Erradicadas: {self.eradicated}")
        self.log_msg(f"Mazos: Jugador({len(self.player_deck.deck)}), Infección({len(self.infection_deck.deck)})")
        self.log_msg("Jugadores:")
        for p in self.players:
            self.log_msg(f" - {p}")
        if self.game_over:
            self.log_msg(f"*** JUEGO TERMINADO: {self.defeat_reason or 'Victoria'} ***")
        self.log_msg("================================\n")

# =============================================================================
# PARTE 2: LÓGICA DE LA INTERFAZ GRÁFICA (PYGAME)
# =============================================================================

class PandemicGUI:
    def __init__(self, game: Game):
        self.game = game
        pygame.init()
        pygame.display.set_caption("Pandemic")

        # Configuración de pantalla y assets
        self.screen_size = (1280, 800)
        self.screen = pygame.display.set_mode(self.screen_size)
        try:
            self.map_image = pygame.image.load("map.png").convert()
            # Escalar la imagen si no coincide con el tamaño de la pantalla
            self.map_image = pygame.transform.scale(self.map_image, self.screen_size)
        except pygame.error:
            self.map_image = pygame.Surface(self.screen_size)
            self.map_image.fill((20, 20, 50))  # Fondo azul oscuro si no hay mapa
            print("ADVERTENCIA: No se encontró 'map.png'. Se usará un fondo de color.")

        # Fuentes
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_medium = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        
        # Colores
        self.colors = {
            "Blue": (0, 100, 255), "Yellow": (255, 255, 0),
            "Black": (50, 50, 50), "Red": (255, 0, 0),
            "White": (255, 255, 255), "UI_BG": (10, 10, 20, 200),
            "Text": (200, 200, 220)
        }

        # Coordenadas de las ciudades en el mapa (x, y)
        self.city_coords = {
            "Atlanta": (275, 330), "Chicago": (240, 280), "Washington": (360, 340),
            "San Francisco": (120, 290), "Montreal": (330, 280), "New York": (380, 295),
            "London": (535, 250), "Madrid": (530, 320), "Paris": (590, 280),
            "Los Angeles": (160, 380), "Mexico City": (220, 420), "Miami": (320, 420),
            "Sao Paulo": (420, 550), "Lagos": (560, 470),
            "Cairo": (680, 380), "Istanbul": (690, 330), "Algiers": (590, 370),
            "Moscow": (780, 280), "Tehran": (820, 330),
            "Beijing": (980, 260), "Seoul": (1050, 260), "Tokyo": (1120, 290),
            "Shanghai": (990, 320), "Hong Kong": (1000, 390),
            # --- Completa el resto de ciudades si quieres mostrarlas en el mapa ---
        }

        # Estado de la UI
        self.planned_actions: List[Tuple[str, Optional[str]]] = []
        self.buttons = self._create_buttons()

    def _create_buttons(self):
        """Crea los rectángulos y textos para los botones de la UI."""
        buttons = {}
        actions = ["Cure", "Build", "Discover Cure", "Share", "Shuttle"]
        y_pos = 650
        for i, action in enumerate(actions):
            buttons[action.lower()] = {
                "rect": pygame.Rect(50 + i * 150, y_pos, 140, 40),
                "text": action,
                "action": (action.lower().replace(" ", "_"), None)
            }
        
        buttons["execute"] = {"rect": pygame.Rect(900, 700, 150, 50), "text": "Execute Turn"}
        buttons["clear"] = {"rect": pygame.Rect(900, 640, 150, 50), "text": "Clear Actions"}
        return buttons

    def run(self):
        """Bucle principal del juego."""
        running = True
        clock = pygame.time.Clock()

        while running:
            # 1. Manejo de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game.game_over:
                    self.handle_click(event.pos)

            # 2. Dibujar todo en pantalla
            self.draw()

            # 3. Actualizar pantalla
            pygame.display.flip()
            clock.tick(30)  # Limitar a 30 FPS

        pygame.quit()

    def handle_click(self, pos):
        """Procesa un clic del ratón."""
        # Comprobar si se ha pulsado un botón de la UI
        for name, btn in self.buttons.items():
            if btn["rect"].collidepoint(pos):
                if name == "execute":
                    if self.planned_actions:
                        self.game.run_turn(self.planned_actions)
                        self.planned_actions = []
                elif name == "clear":
                    self.planned_actions = []
                elif len(self.planned_actions) < 4:
                    self.planned_actions.append(btn["action"])
                return

        # Comprobar si se ha pulsado una ciudad
        for city_name, city_pos in self.city_coords.items():
            if pygame.Rect(city_pos[0]-10, city_pos[1]-10, 20, 20).collidepoint(pos):
                if len(self.planned_actions) < 4:
                    # Por simplicidad, un clic en ciudad siempre es un 'move'.
                    self.planned_actions.append(("move", city_name))
                return

    def draw(self):
        """Dibuja todos los elementos en la pantalla."""
        # Fondo
        self.screen.blit(self.map_image, (0, 0))

        # Dibujar elementos del mapa
        self.draw_connections()
        self.draw_cities()
        self.draw_players()
        
        # Dibujar UI
        self.draw_ui_panels()
        self.draw_player_hand()
        self.draw_planned_actions()
        self.draw_buttons()
        self.draw_game_state()
        self.draw_log()

        if self.game.game_over:
            self.draw_game_over()

    def draw_connections(self):
        for city_name, city_pos in self.city_coords.items():
            city_obj = self.game.cities.get(city_name.lower())
            if not city_obj:
                continue
            
            for neighbor_name in city_obj.neighbors:
                neighbor_pos = self.city_coords.get(neighbor_name)
                if neighbor_pos:
                    # Conexiones transpacíficas (casos especiales)
                    if (city_name == "San Francisco" and neighbor_name == "Tokyo") or \
                       (city_name == "Los Angeles" and neighbor_name == "Sydney"):
                        pygame.draw.line(self.screen, self.colors["White"], city_pos, (0, neighbor_pos[1]), 2)
                        pygame.draw.line(self.screen, self.colors["White"], (self.screen_size[0], city_pos[1]), neighbor_pos, 2)
                    else:
                        pygame.draw.line(self.screen, self.colors["White"], city_pos, neighbor_pos, 1)

    def draw_cities(self):
        for city_name, city_pos in self.city_coords.items():
            city_obj = self.game.cities.get(city_name.lower())
            if not city_obj:
                continue

            # Dibujar estación de investigación (un cuadrado blanco debajo)
            if city_name in self.game.research_stations:
                pygame.draw.rect(self.screen, self.colors["White"], (city_pos[0]-8, city_pos[1]-8, 16, 16))

            # Dibujar cubos de infección
            if city_obj.infections > 0:
                color = self.colors[city_obj.color]
                for i in range(city_obj.infections):
                    pygame.draw.rect(self.screen, color, (city_pos[0] + 10 + i * 12, city_pos[1] - 10, 10, 10))
                # Contador numérico
                count_text = self.font_medium.render(str(city_obj.infections), True, self.colors["White"])
                self.screen.blit(count_text, (city_pos[0] + 12, city_pos[1] - 30))

            # Nombre de la ciudad
            text = self.font_small.render(city_name, True, self.colors["Text"])
            pygame.draw.rect(self.screen, self.colors["Black"], (city_pos[0]-2, city_pos[1]-2, text.get_width()+4, text.get_height()+4))
            self.screen.blit(text, city_pos)

    def draw_players(self):
        player_colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
        for i, player in enumerate(self.game.players):
            pos = self.city_coords.get(player.location)
            if pos:
                pygame.draw.circle(self.screen, player_colors[i], (pos[0] - 10 - i*5, pos[1] + 10), 8)
                p_text = self.font_small.render(f"P{i+1}", True, self.colors["Black"])
                self.screen.blit(p_text, (pos[0] - 15 - i*5, pos[1] + 5))

    def draw_ui_panels(self):
        # Panel inferior para acciones y mano
        s = pygame.Surface((self.screen_size[0], 200))
        s.set_alpha(200)
        s.fill(self.colors["UI_BG"])
        self.screen.blit(s, (0, self.screen_size[1] - 200))

    def draw_player_hand(self):
        if not self.game.players:
            return
        player = self.game.players[self.game.current_player_index]
        title = self.font_medium.render(f"Turno de {player.name} - Mano:", True, self.colors["Text"])
        self.screen.blit(title, (50, self.screen_size[1] - 180))
        
        for i, card in enumerate(player.hand):
            try:
                color = self.colors[self.game.cities[card.lower()].color]
            except KeyError:
                color = self.colors["White"]  # Para cartas de evento
            
            card_text = self.font_small.render(card, True, self.colors["Black"])
            card_rect = pygame.Rect(50 + i * 110, self.screen_size[1] - 150, 100, 50)
            pygame.draw.rect(self.screen, color, card_rect)
            self.screen.blit(card_text, (card_rect.x + 5, card_rect.y + 5))

    def draw_planned_actions(self):
        title = self.font_medium.render("Acciones Planeadas:", True, self.colors["Text"])
        self.screen.blit(title, (900, self.screen_size[1] - 180))
        for i, (action, param) in enumerate(self.planned_actions):
            text = f"{i+1}. {action} {param or ''}"
            action_text = self.font_small.render(text, True, self.colors["Text"])
            self.screen.blit(action_text, (900, self.screen_size[1] - 160 + i * 20))
    
    def draw_buttons(self):
        for btn in self.buttons.values():
            pygame.draw.rect(self.screen, self.colors["Blue"], btn["rect"])
            text = self.font_medium.render(btn["text"], True, self.colors["White"])
            self.screen.blit(text, (btn["rect"].x + 10, btn["rect"].y + 10))

    def draw_game_state(self):
        # Estado de curas, brotes, etc.
        outbreak_text = f"Brotes: {self.game.outbreaks}/8"
        rate_text = f"Ritmo Infección: {self.game.infection_rate_list[self.game.infection_rate_index]}"
        
        self.screen.blit(self.font_medium.render(outbreak_text, True, self.colors["Red"]), (20, 20))
        self.screen.blit(self.font_medium.render(rate_text, True, self.colors["Yellow"]), (20, 50))
        
        for i, (color, discovered) in enumerate(self.game.cures_discovered.items()):
            pos = (200 + i * 100, 20)
            pygame.draw.rect(self.screen, self.colors[color], (pos[0], pos[1], 80, 30), border_radius=5)
            if discovered:
                status = "CURADA" if not self.game.eradicated[color] else "ERRADICADA"
                cure_text = self.font_small.render(status, True, self.colors["Black"])
                self.screen.blit(cure_text, (pos[0] + 10, pos[1] + 8))

    def draw_log(self):
        log_surface = pygame.Surface((300, 200))
        log_surface.set_alpha(180)
        log_surface.fill(self.colors["UI_BG"])
        self.screen.blit(log_surface, (self.screen_size[0] - 310, 10))

        # Mostrar solo las últimas ~9 líneas para que quepan
        for i, msg in enumerate(self.game.log[-9:]):
            log_text = self.font_small.render(msg, True, self.colors["Text"])
            self.screen.blit(log_text, (self.screen_size[0] - 300, 20 + i * 18))

    def draw_game_over(self):
        s = pygame.Surface(self.screen_size)
        s.set_alpha(200)
        s.fill(self.colors["Black"])
        self.screen.blit(s, (0, 0))
        
        text = self.font_large.render("JUEGO TERMINADO", True, self.colors["Red"])
        reason = self.font_medium.render(self.game.defeat_reason or "Fin de la partida", True, self.colors["White"])
        
        self.screen.blit(text, (self.screen_size[0]/2 - text.get_width()/2, self.screen_size[1]/2 - 50))
        self.screen.blit(reason, (self.screen_size[0]/2 - reason.get_width()/2, self.screen_size[1]/2))

# =============================================================================
# PARTE 3: BUCLE PRINCIPAL
# =============================================================================

def main():
    # 1. Inicializar el núcleo del juego
    game = Game(seed=42)
    game.add_player("Jugador 1")
    #game.add_player("Jugador 2")  # Descomenta para añadir más jugadores
    game.research_stations.append("Atlanta")  # Estación inicial

    # 2. Inicializar y correr la GUI
    gui = PandemicGUI(game)
    gui.run()

if __name__ == "__main__":
    main()
