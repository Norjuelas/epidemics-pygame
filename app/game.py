import random
from typing import List, Dict, Tuple, Any, Optional
from app.core import InfectionDeck, PlayerDeck, Player, City
from app.config import EVENT_NAMES, EVENT_DISPLAY_NAMES

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
