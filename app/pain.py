import pygame
import random
import sys
import traceback 
from typing import Dict, List, Optional, Tuple, Any

# versión con UI funcional v0.6 (Discard Modal + Fixes)

# =============================================================================
# PARTE 1: LÓGICA DEL JUEGO (NÚCLEO v0.4 ES)
# =============================================================================

EVENT_NAMES = [
    "POBLACION_RESILIENTE",
    "PUENTE_AEREO",
    "SUBSIDIO_GUBERNAMENTAL",
    "PREDICCION",
    "UNA_NOCHE_TRANQUILA"
]

EVENT_DISPLAY_NAMES = {
    "POBLACION_RESILIENTE": "Población Resiliente",
    "PUENTE_AEREO": "Puente Aéreo",
    "SUBSIDIO_GUBERNAMENTAL": "Subsidio Gubernamental",
    "PREDICCION": "Predicción",
    "UNA_NOCHE_TRANQUILA": "Una Noche Tranquila"
}

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
        if not self.deck: raise IndexError("Mazo de Infección vacío")
        return self.deck.pop(0)

    def draw_bottom(self) -> str:
        if not self.deck: raise IndexError("Mazo de Infección vacío")
        return self.deck.pop()

    def discard(self, card: str):
        self.discard_pile.append(card)

    def remove_from_discard(self, card_name: str):
        if card_name in self.discard_pile:
            self.discard_pile.remove(card_name)

    def peek_top(self, n: int) -> List[str]:
        return self.deck[:n]

    def modify_top(self, new_top_cards: List[str]):
        n = len(new_top_cards)
        self.deck = new_top_cards + self.deck[n:]

    def shuffle_discard_onto_deck_top(self):
        if not self.discard_pile: return
        random.shuffle(self.discard_pile)
        self.deck = self.discard_pile + self.deck
        self.discard_pile = []

class PlayerDeck:
    def __init__(self, cities: List[str], n_epidemics: int = 4, n_events: int = 5, seed: Optional[int] = None):
        if seed is not None: random.seed(seed)
        base = list(cities)
        
        events_to_add = EVENT_NAMES[:n_events]
        while len(events_to_add) < n_events:
             events_to_add.append(EVENT_NAMES[len(events_to_add) % 5])
             
        base.extend(events_to_add)
        random.shuffle(base)
        
        piles: List[List[str]] = []
        n = n_epidemics
        pile_size = max(1, len(base) // n)
        for i in range(n):
            pile = base[i*pile_size:(i+1)*pile_size]
            pile.append("EPIDEMIA")
            random.shuffle(pile)
            piles.append(pile)
        
        # Add leftovers
        if n * pile_size < len(base):
             leftover = base[n*pile_size:]
             if piles: piles[-1].extend(leftover)

        self.deck: List[str] = [card for pile in piles for card in pile]
        self.discard_pile: List[str] = []

    def draw_card(self) -> str:
        if not self.deck: raise IndexError("Mazo de Jugador vacío")
        return self.deck.pop(0)

    def discard(self, card: str):
        self.discard_pile.append(card)

class Game:
    MAX_RESEARCH_STATIONS = 6
    PLAYER_HAND_LIMIT = 7

    def __init__(self, num_players: int = 2, seed: int = 42):
        print(f"DEBUG: Inicializando juego con semilla {seed}...")
        random.seed(seed)

        self.num_players = num_players
        self.log: List[str] = []
        self.cities: Dict[str, City] = {}
        self.players: List[Player] = []
        self.current_player_index = 0

        self.infection_rate_list = [2, 2, 2, 3, 3, 4, 4]
        self.infection_rate_index = 0
        self.outbreaks = 0
        self.turn = 1

        self.game_over = False
        self.defeat_reason: Optional[str] = None
        
        self.skip_next_infection_phase = False

        self.research_stations: List[str] = []
        self.cures_discovered: Dict[str, bool] = {"Blue": False, "Yellow": False, "Black": False, "Red": False}
        self.eradicated: Dict[str, bool] = {"Blue": False, "Yellow": False, "Black": False, "Red": False}

        print("DEBUG: Configurando mapa...")
        self._setup_full_map()
        city_names = [c.name for c in self.cities.values()]
        
        print("DEBUG: Creando mazos...")
        self.infection_deck = InfectionDeck(city_names)
        self.player_deck = PlayerDeck(city_names, seed=seed)
        
        print("DEBUG: Infecciones iniciales...")
        self._initial_infections()
        
        self.research_stations.append("Atlanta")
        for i in range(num_players):
            self.add_player(f"Jugador {i+1}", "Atlanta")
        print("DEBUG: Juego inicializado correctamente.")

    def log_msg(self, text: str):
        print(text)
        self.log.append(text)
        if len(self.log) > 500:
            self.log.pop(0)

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
        red = ["Bangkok","Jakarta","Ho Chi Minh","Hong Kong","Shanghai","Beijing","Seoul","Tokyo","Osaka","Taipei","Manila","Sydney"]
        for name in blue: self._add_city(name, "Blue")
        for name in yellow: self._add_city(name, "Yellow")
        for name in black: self._add_city(name, "Black")
        for name in red: self._add_city(name, "Red")
        connections = [
            ("San Francisco", ["Tokyo", "Manila", "Los Angeles", "Chicago"]),
            ("Chicago", ["San Francisco", "Los Angeles", "Mexico City", "Atlanta", "Montreal"]),
            ("Atlanta", ["Chicago", "Washington", "Miami"]),
            ("Montreal", ["Chicago", "New York", "Washington"]),
            ("New York", ["Montreal", "Washington", "London", "Madrid"]),
            ("Washington", ["Atlanta", "New York", "Montreal", "Miami"]),
            ("London", ["New York", "Madrid", "Paris", "Essen"]),
            ("Madrid", ["New York", "London", "Paris", "Algiers", "Sao Paulo"]),
            ("Paris", ["London", "Essen", "Milan", "Algiers", "Madrid"]),
            ("Essen", ["London", "Paris", "Milan", "St. Petersburg"]),
            ("Milan", ["Essen", "Paris", "Istanbul"]),
            ("St. Petersburg", ["Essen", "Istanbul", "Moscow"]),
            ("Los Angeles", ["San Francisco", "Chicago", "Mexico City", "Sydney"]),
            ("Mexico City", ["Los Angeles", "Chicago", "Miami", "Bogota", "Lima"]),
            ("Miami", ["Atlanta", "Washington", "Mexico City", "Bogota"]),
            ("Bogota", ["Mexico City", "Miami", "Lima", "Buenos Aires", "Sao Paulo"]),
            ("Lima", ["Mexico City", "Bogota", "Santiago"]),
            ("Santiago", ["Lima"]),
            ("Buenos Aires", ["Bogota", "Sao Paulo"]),
            ("Sao Paulo", ["Buenos Aires", "Bogota", "Madrid", "Lagos"]),
            ("Lagos", ["Sao Paulo", "Khartoum", "Kinshasa"]),
            ("Khartoum", ["Lagos", "Kinshasa", "Johannesburg", "Cairo"]),
            ("Kinshasa", ["Lagos", "Khartoum", "Johannesburg"]),
            ("Johannesburg", ["Kinshasa", "Khartoum"]),
            ("Algiers", ["Madrid", "Paris", "Istanbul", "Cairo"]),
            ("Istanbul", ["Milan", "St. Petersburg", "Moscow", "Baghdad", "Cairo", "Algiers"]),
            ("Moscow", ["St. Petersburg", "Istanbul", "Tehran"]),
            ("Cairo", ["Algiers", "Istanbul", "Baghdad", "Khartoum", "Riyadh"]),
            ("Baghdad", ["Istanbul", "Tehran", "Karachi", "Riyadh", "Cairo"]),
            ("Tehran", ["Moscow", "Baghdad", "Karachi", "Delhi"]),
            ("Karachi", ["Tehran", "Baghdad", "Riyadh", "Mumbai", "Delhi"]),
            ("Riyadh", ["Cairo", "Baghdad", "Karachi"]),
            ("Delhi", ["Tehran", "Karachi", "Mumbai", "Chennai", "Kolkata"]),
            ("Mumbai", ["Karachi", "Delhi", "Chennai"]),
            ("Chennai", ["Mumbai", "Delhi", "Kolkata", "Bangkok", "Jakarta"]),
            ("Kolkata", ["Delhi", "Chennai", "Bangkok", "Hong Kong"]),
            ("Bangkok", ["Kolkata", "Chennai", "Jakarta", "Ho Chi Minh", "Hong Kong"]),
            ("Jakarta", ["Chennai", "Bangkok", "Ho Chi Minh", "Sydney"]),
            ("Ho Chi Minh", ["Jakarta", "Bangkok", "Hong Kong", "Manila"]),
            ("Hong Kong", ["Kolkata", "Bangkok", "Ho Chi Minh", "Shanghai", "Taipei", "Manila"]),
            ("Shanghai", ["Beijing", "Seoul", "Tokyo", "Hong Kong", "Taipei"]),
            ("Beijing", ["Shanghai", "Seoul"]),
            ("Seoul", ["Beijing", "Shanghai", "Tokyo"]),
            ("Tokyo", ["Seoul", "Shanghai", "Osaka", "San Francisco"]),
            ("Osaka", ["Tokyo", "Taipei"]),
            ("Taipei", ["Osaka", "Shanghai", "Hong Kong", "Manila"]),
            ("Manila", ["Taipei", "Hong Kong", "Ho Chi Minh", "Sydney", "San Francisco"]),
            ("Sydney", ["Jakarta", "Manila", "Los Angeles"])
        ]
        for city_name, neighs in connections:
            for nb in neighs:
                try:
                    self._connect(city_name, nb)
                except ValueError:
                    pass

    def _initial_infections(self):
        self.log_msg("\n--- Infecciones Iniciales ---")
        for i in range(3):
            city_card = self.infection_deck.draw_top()
            self.infect_city(city_card, 3 - i, source="initial")
            self.infection_deck.discard(city_card)
        for i in range(3):
            city_card = self.infection_deck.draw_top()
            self.infect_city(city_card, 1, source="initial")
            self.infection_deck.discard(city_card)
        self.log_msg("-----------------------------\n")

    def _outbreak_chain(self, city_key: str, visited: set):
        if city_key in visited: return
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
            if self.eradicated.get(nb_city.color, False): continue
            
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
        
        cards_to_deal = {2: 4, 3: 3, 4: 2}.get(self.num_players, 2)

        p = Player(player_name, self.cities[key].name)
        self.players.append(p)
        self.log_msg(f"Añadiendo {p.name} en {self.cities[key].name}. Repartiendo {cards_to_deal} cartas...")
        try:
            for _ in range(cards_to_deal):
                card = self.player_deck.draw_card()
                if card == "EPIDEMIA":
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
    
    def transfer_card(self, giver: Player, receiver: Player, card_name: str):
        if card_name in giver.hand:
            giver.hand.remove(card_name)
            receiver.hand.append(card_name)
            self.log_msg(f"[ACCIÓN] {giver.name} dio {card_name} a {receiver.name}.")
            return True
        return False
        
    def play_event(self, player_index: int, card_name: str, **kwargs):
        player = self.players[player_index]
        if card_name not in player.hand:
            return False
        
        player.hand.remove(card_name)
        self.player_deck.discard(card_name)
        self.log_msg(f"[EVENTO] {player.name} jugó {EVENT_DISPLAY_NAMES.get(card_name, card_name)}.")
        
        if card_name == "UNA_NOCHE_TRANQUILA":
            self.skip_next_infection_phase = True
            self.log_msg(" -> La próxima fase de infección será omitida.")
            
        elif card_name == "POBLACION_RESILIENTE":
            target = kwargs.get('target_card')
            if target:
                self.infection_deck.remove_from_discard(target)
                self.log_msg(f" -> {target} eliminada de la partida (Resiliente).")
        
        elif card_name == "SUBSIDIO_GUBERNAMENTAL":
            target_city = kwargs.get('target_city')
            if target_city and target_city not in self.research_stations:
                 if len(self.research_stations) < self.MAX_RESEARCH_STATIONS:
                     self.research_stations.append(target_city)
                     self.log_msg(f" -> Estación construida en {target_city}.")
        
        elif card_name == "PUENTE_AEREO":
            p_idx = kwargs.get('target_player_idx')
            dest = kwargs.get('dest_city')
            if p_idx is not None and dest:
                self.players[p_idx].move_to(dest)
                self.log_msg(f" -> {self.players[p_idx].name} movido a {dest}.")
                
        elif card_name == "PREDICCION":
            new_order = kwargs.get('new_order')
            if new_order:
                self.infection_deck.modify_top(new_order)
                self.log_msg(" -> Mazo de infección reordenado.")

        return True

    def validate_turn_plan(self, player_index: int, actions: List[Tuple[str, Any]]) -> bool:
        p = self.players[player_index]
        sim_loc = p.location
        sim_hand = p.hand[:]
        sim_stations = self.research_stations[:]
        
        for i, (act, param) in enumerate(actions, 1):
            act = act.lower()
            
            if act == "event":
                card_name = param.get("name")
                kwargs = param.get("kwargs", {})
                
                if card_name in sim_hand: 
                    sim_hand.remove(card_name)
                else:
                    return False
                
                if card_name == "PUENTE_AEREO":
                    t_idx = kwargs.get('target_player_idx')
                    dest = kwargs.get('dest_city')
                    if t_idx == player_index and dest:
                        sim_loc = dest
                elif card_name == "SUBSIDIO_GUBERNAMENTAL":
                    target = kwargs.get('target_city')
                    if target and target not in sim_stations:
                        sim_stations.append(target)
                continue

            if act == "move":
                try:
                    dest_obj = self._get_city(param)
                    src_obj = self._get_city(sim_loc)
                    if dest_obj.name not in src_obj.neighbors:
                        return False
                    sim_loc = dest_obj.name
                except: return False
                
            elif act == "direct_flight":
                if not param: return False
                found = False
                for c in sim_hand:
                    if c.lower() == param.lower():
                        sim_hand.remove(c)
                        sim_loc = param 
                        found = True
                        break
                if not found: return False
                
            elif act == "charter_flight":
                if not param: return False
                found = False
                for c in sim_hand:
                    if c.lower() == sim_loc.lower():
                        sim_hand.remove(c)
                        sim_loc = param
                        found = True
                        break
                if not found: return False
                
            elif act == "shuttle":
                if not param: return False
                if sim_loc not in sim_stations or param not in sim_stations:
                    return False
                sim_loc = param
                
            elif act == "build":
                if sim_loc in sim_stations: return False
                if len(sim_stations) >= Game.MAX_RESEARCH_STATIONS: return False
                found = False
                for c in sim_hand:
                    if c.lower() == sim_loc.lower():
                        sim_hand.remove(c)
                        sim_stations.append(sim_loc)
                        found = True
                        break
                if not found: return False
                
            elif act in ("cure", "treat", "share"):
                pass
                
            elif act == "discover_cure":
                if sim_loc not in sim_stations: return False
                colors = {"Blue": 0, "Yellow": 0, "Black": 0, "Red": 0}
                for c in sim_hand:
                    if c.lower() in self.cities:
                        col = self.cities[c.lower()].color
                        colors[col] += 1
                can_cure = any(k >= 5 for k in colors.values())
                if not can_cure: return False
                
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
    
    # --- Modificado para no descartar automáticamente ---
    def _player_draw_card_to_hand(self, player: Player) -> bool:
        try:
            card = self.player_deck.draw_card()
        except IndexError:
            self.game_over = True
            self.defeat_reason = "Sin cartas en el mazo de jugador"
            self.log_msg(f"[DERROTA] {self.defeat_reason}")
            return False
        if card in EVENT_NAMES:
            self.log_msg(f"[ROBO] {player.name} robó Evento: {EVENT_DISPLAY_NAMES[card]}.")
            player.hand.append(card)
        elif card == "EPIDEMIA":
            self.player_deck.discard(card)
            self._handle_epidemic()
            if self.game_over: return False
        else:
            self.log_msg(f"[ROBO] {player.name} robó: {card}.")
            player.hand.append(card)
        
        # ELIMINADO: Bucle de descarte automático. Ahora la GUI gestiona el descarte.
        return True

    def infection_phase(self):
        if self.game_over: return
        
        if self.skip_next_infection_phase:
            self.log_msg("[EVENTO] Fase de infección omitida por 'Una Noche Tranquila'.")
            self.skip_next_infection_phase = False
            return

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

    # --- Reorganizado para dividir ejecución de acciones y final de turno ---
    def execute_turn_actions(self, actions: List[Tuple[str, Any]], player_index: Optional[int] = None):
        if self.game_over: return False
        if player_index is None: player_index = self.current_player_index
        player = self.players[player_index]
        self.log_msg(f"\n--- Ejecutando turno de {player.name} ---")
        
        actions_allowed = 4
        used = 0
        
        for i, (act, param) in enumerate(actions, 1):
            act = act.lower()
            
            # Events are free actions
            if act == "event":
                card_name = param["name"]
                kwargs = param["kwargs"]
                self.play_event(player_index, card_name, **kwargs)
                continue
            
            # Standard actions
            if used >= actions_allowed: break
            self.log_msg(f"Acción: {act} {param or ''}")
            ok = self.perform_action((act, param), player_index)
            if ok: used += 1
            
            if all(self.cures_discovered.values()):
                self.game_over = True
                self.log_msg("[VICTORIA] ¡Se descubrieron las 4 curas! ¡Habéis ganado!")
                return True
                
            if self.game_over: return True
        return True

    def draw_phase_cards(self):
        player = self.players[self.current_player_index]
        self.log_msg(f"\n--- Fase de Robo ({player.name}) ---")
        if not self._player_draw_card_to_hand(player): return
        if not self._player_draw_card_to_hand(player): return
    
    def check_hand_limit(self):
        player = self.players[self.current_player_index]
        return len(player.hand) > self.PLAYER_HAND_LIMIT

    def player_discard(self, card_name):
        player = self.players[self.current_player_index]
        if card_name in player.hand:
            player.hand.remove(card_name)
            self.player_deck.discard(card_name)
            self.log_msg(f" -> {player.name} descartó {card_name} (exceso).")

    def end_turn_sequence(self):
        if self.game_over: return
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

    def perform_action(self, action: Tuple[str, Any], player_index: int = 0) -> bool:
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
                self.log_msg(f"[ACCIÓN] Movimiento inválido.")
                return False
            except (ValueError, TypeError):
                return False

        elif act in ("cure", "treat"):
            city = self._get_city(player.location)
            if city.infections == 0:
                self.log_msg(f"[ACCIÓN] No hay infecciones que tratar.")
                return False
            color = city.color
            remove_amount = 3 if self.cures_discovered.get(color, False) else 1
            removed = min(city.infections, remove_amount)
            city.infections -= removed
            self.log_msg(f"[ACCIÓN] {player.name} trató {city.name}, quitando {removed} cubos.")
            self._check_and_set_eradication(color)
            return True

        elif act == "build":
            city_name = player.location
            if city_name in self.research_stations: return False
            if city_name not in player.hand: return False
            if len(self.research_stations) >= Game.MAX_RESEARCH_STATIONS: return False
            self.research_stations.append(city_name)
            player.hand.remove(city_name)
            self.player_deck.discard(city_name)
            self.log_msg(f"[ACCIÓN] {player.name} construyó Estación en {city_name}.")
            return True

        elif act == "discover_cure":
            city = self._get_city(player.location)
            if city.name not in self.research_stations: return False
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
                    self.log_msg(f"[CURA DESCUBIERTA] ¡Cura {col} descubierta!")
                    self._check_and_set_eradication(col)
                    return True
            return False

        elif act == "share":
            return True

        elif act == "shuttle":
            try:
                self._get_city(param)
                return self.shuttle(player_index, param)
            except: return False

        elif act == "skip":
            self.log_msg(f"[ACCIÓN] {player.name} salta una acción.")
            return True
        
        elif act == "direct_flight":
            dest_name = param
            if not dest_name: return False
            player = self.players[player_index]
            card_found = None
            for card in player.hand:
                if card.lower() == dest_name.lower():
                    card_found = card
                    break
            if not card_found: return False
            player.move_to(dest_name)
            player.hand.remove(card_found)
            self.player_deck.discard(card_found)
            self.log_msg(f"[ACCIÓN] {player.name} Vuelo Directo a {dest_name}.")
            return True

        elif act == "charter_flight":
            dest_name = param
            if not dest_name: return False
            player = self.players[player_index]
            origin = player.location
            origin_card_found = None
            for card in player.hand:
                if card.lower() == origin.lower():
                    origin_card_found = card
                    break
            if not origin_card_found: return False
            player.move_to(dest_name)
            player.hand.remove(origin_card_found)
            self.player_deck.discard(origin_card_found)
            self.log_msg(f"[ACCIÓN] {player.name} Vuelo Charter a {dest_name}.")
            return True

        else:
            return False

# =============================================================================
# PARTE 2: LÓGICA DE LA INTERFAZ GRÁFICA (PYGAME)
# =============================================================================

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
    def __init__(self, game_ref, callback_confirm, callback_cancel):
        self.game = game_ref
        self.on_confirm = callback_confirm
        self.on_cancel = callback_cancel
        self.width = 900
        self.height = 600
        self.bg_color = (30, 30, 40)
        self.border_color = (100, 100, 100)
        
        self.current_player = self.game.players[self.game.current_player_index]
        self.location = self.current_player.location
        
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
                for i, card in enumerate(self.current_player.hand):
                    r = pygame.Rect(50 + i * 110, base_y + 30, 100, 40)
                    if r.collidepoint(rel_x, rel_y):
                         if card.lower() == self.location.lower(): 
                             self.selected_card = (card, self.current_player)
                
                base_y = 300
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
            msg = font_text.render("No hay otros jugadores en esta ciudad.", True, (200, 200, 200))
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
            # Current Player Hand
            y_base = 150
            lbl = font_text.render(f"Tu Mano (Dar carta '{self.location}'):", True, (200, 200, 200))
            modal_surface.blit(lbl, (50, y_base))
            
            for i, card in enumerate(self.current_player.hand):
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

class MainMenu:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.bg_color = (20, 20, 30)
        self.text_color = (255, 255, 255)
        self.btn_color = (0, 100, 200)
        self.btn_hover = (0, 150, 250)
        
        try:
            self.bg_image = pygame.image.load("menu.png").convert()
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
        self.map_image = load_image_or_create_fallback("map.png", self.screen_size, (20, 20, 50))

        # 2. Player Images
        self.player_images = []
        for i in range(1, 5):
            img = load_image_or_create_fallback(f"ficha{i}.png", (16, 30), (255, 255, 255, 128))
            self.player_images.append(img)

        # 3. Disease/City Markers
        self.city_colors_imgs = {}
        files_map = {
            "Blue": ("azul.png", "centro_azul.png", (0, 100, 255)),
            "Yellow": ("amarillo.png", "centro_amarillo.png", (255, 255, 0)),
            "Black": ("negro.png", "centro_negro.png", (50, 50, 50)),
            "Red": ("rojo.png", "centro_rojo.png", (255, 0, 0))
        }
        
        for c_name, (norm_file, center_file, fallback_color) in files_map.items():
            # Standard
            self.city_colors_imgs[c_name] = load_image_or_create_fallback(norm_file, (30, 30), fallback_color)
            
            # Center
            center_img = load_image_or_create_fallback(center_file, (30, 30), fallback_color)
            self.city_colors_imgs[c_name + "_Center"] = center_img
        
        # 4. Track Markers
        # Updated per request: Track 309x38, Marker 70x70
        self.infection_track_img = load_image_or_create_fallback("infection_track_mark.png", (309, 38), (100, 100, 100))
        self.infection_marker_img = load_image_or_create_fallback("infection.png", (70, 70), (255, 50, 50))

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
                self._on_modal_cancel)
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

# =============================================================================
# PARTE 3: BUCLE PRINCIPAL
# =============================================================================

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