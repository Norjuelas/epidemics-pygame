# pandemic_v0_4.py
"""
Pandemic v0.4 (consola) - Versión final del núcleo jugable (sin GUI)
Basado en v0.3; añade:
 - share_knowledge (intercambio de cartas)
 - shuttle (vuelo entre estaciones de investigación)
 - erradicación de enfermedades
 - EVENT_X mensajes informativos
 - integración completa en Game.run_turn()
 - resumen y mensajes [BROTE], [EPIDEMIA], [CURA], [ERRADICADA], [DERROTA], [VICTORIA]
"""
import random
from typing import Dict, List, Optional, Tuple

# ---------------------------
# Clases base (City, Player)
# ---------------------------
class City:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'Blue', 'Yellow', 'Black', 'Red'
        self.infections = 0  # 0..3
        self.neighbors: List[str] = []

    def add_neighbor(self, other_city_name: str):
        if other_city_name not in self.neighbors:
            self.neighbors.append(other_city_name)

    def __repr__(self):
        return f"City({self.name}, {self.color}, inf={self.infections})"


class Player:
    def __init__(self, name: str, start_city: str):
        self.name = name
        self.location = start_city
        self.hand: List[str] = []  # cartas en mano (city names, EVENT_x, EPIDEMIC)

    def move_to(self, city_name: str):
        self.location = city_name

    def __repr__(self):
        return f"Player({self.name} @ {self.location} | hand={len(self.hand)})"


# ---------------------------
# InfectionDeck
# ---------------------------
class InfectionDeck:
    def __init__(self, cities: List[str]):
        self.deck: List[str] = list(cities)
        random.shuffle(self.deck)
        self.discard_pile: List[str] = []

    def draw_top(self) -> str:
        if not self.deck:
            raise IndexError("InfectionDeck vacío al intentar robar top.")
        return self.deck.pop(0)

    def draw_bottom(self) -> str:
        if not self.deck:
            raise IndexError("InfectionDeck vacío al intentar robar bottom.")
        return self.deck.pop()

    def discard(self, card: str):
        self.discard_pile.append(card)

    def shuffle_discard_onto_deck_top(self):
        if not self.discard_pile:
            return
        print("[InfectionDeck] Barajando descarte y colocándolo encima del mazo.")
        temp = list(self.discard_pile)
        random.shuffle(temp)
        self.deck = temp + self.deck
        self.discard_pile = []

    def status(self):
        return {"deck": len(self.deck), "discard": len(self.discard_pile)}


# ---------------------------
# PlayerDeck (con setup de epidemias)
# ---------------------------
class PlayerDeck:
    def __init__(self, cities: List[str], n_epidemics: int = 6, n_events: int = 5, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        base = list(cities)
        # añadir cartas evento
        for i in range(1, n_events + 1):
            base.append(f"EVENT_{i}")
        random.shuffle(base)
        # dividir en pilas y añadir EPIDEMIC
        piles: List[List[str]] = []
        n = n_epidemics
        pile_size = len(base) // n
        remainder = len(base) % n
        idx = 0
        for i in range(n):
            size = pile_size + (1 if i < remainder else 0)
            piles.append(base[idx: idx + size])
            idx += size
        for i in range(n):
            piles[i].append("EPIDEMIC")
            random.shuffle(piles[i])
        final_deck = []
        for p in piles:
            final_deck.extend(p)
        self.deck: List[str] = final_deck
        self.discard_pile: List[str] = []

    def draw_card(self) -> str:
        if not self.deck:
            raise IndexError("PlayerDeck vacío al intentar robar carta.")
        return self.deck.pop(0)

    def discard(self, card: str):
        self.discard_pile.append(card)

    def recycle_discard_into_deck(self):
        if not self.discard_pile:
            return
        temp = list(self.discard_pile)
        random.shuffle(temp)
        self.deck.extend(temp)
        self.discard_pile = []

    def status(self):
        return {"deck": len(self.deck), "discard": len(self.discard_pile)}


# ---------------------------
# Game v0.4 (núcleo)
# ---------------------------
class Game:
    MAX_RESEARCH_STATIONS = 6
    PLAYER_HAND_LIMIT = 7

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

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
        self.player_deck = PlayerDeck(city_names)
        # reparto inicial y estado
        self._initial_infections()

    # ---------------------------
    # Mapa (igual que versiones previas)
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
            ("Bangkok", ["Kolkata", "Chennai", "Jakarta", "Ho Chi Minh City", "Hong Kong"]),
            ("Jakarta", ["Chennai", "Bangkok", "Ho Chi Minh City", "Sydney"]),
            ("Ho Chi Minh City", ["Jakarta", "Bangkok", "Hong Kong", "Manila"]),
            ("Hong Kong", ["Kolkata", "Bangkok", "Ho Chi Minh City", "Shanghai", "Taipei", "Manila"]),
            ("Shanghai", ["Beijing", "Seoul", "Tokyo", "Hong Kong", "Taipei"]),
            ("Beijing", ["Shanghai", "Seoul"]),
            ("Seoul", ["Beijing", "Shanghai", "Tokyo"]),
            ("Tokyo", ["Seoul", "Shanghai", "Osaka", "San Francisco"]),
            ("Osaka", ["Tokyo", "Taipei"]),
            ("Taipei", ["Osaka", "Shanghai", "Hong Kong", "Manila"]),
            ("Manila", ["Taipei", "Hong Kong", "Ho Chi Minh City", "Sydney", "San Francisco"]),
            ("Sydney", ["Jakarta", "Manila", "Los Angeles"])
        ]
        for city_name, neighs in connections:
            for nb in neighs:
                try:
                    self._connect(city_name, nb)
                except ValueError:
                    pass

    # ---------------------------
    # Inicializaciones
    # ---------------------------
    def _initial_infections(self):
        cities_keys = list(self.cities.keys())
        sample = random.sample(cities_keys, k=4)
        for k in sample:
            city = self.cities[k]
            add = random.choice([1, 2])
            city.infections = min(3, city.infections + add)
            print(f"[Init] {city.name} inicial recibe {add} cubo(s) (ahora {city.infections}).")

    # ---------------------------
    # --- OUTBREAK CHAIN ---
    # ---------------------------
    def _outbreak_chain(self, city_key: str, visited: set):
        if city_key in visited:
            return
        visited.add(city_key)
        city = self.cities[city_key]
        self.outbreaks += 1
        print(f"[BROTE] {city.name} estalla! Outbreaks = {self.outbreaks}")
        for nb_name in city.neighbors:
            nb_key = nb_name.lower()
            nb_city = self.cities[nb_key]
            if nb_city.infections < 3:
                nb_city.infections += 1
                print(f"  [BROTE->INFECT] {nb_city.name} recibe 1 cubo (ahora {nb_city.infections})")
            else:
                if nb_key not in visited:
                    print(f"  [BROTE->CHAIN] {nb_city.name} también estalla (cadena).")
                    self._outbreak_chain(nb_key, visited)
                else:
                    print(f"  [BROTE->CHAIN] {nb_city.name} ya explotó en esta cadena: no repetir.")

    # ---------------------------
    # Manejo de infecciones (general) - respeta erradicación
    # ---------------------------
    def infect_city(self, city_name: str, cubes: int = 1, source: str = "generic"):
        if self.game_over:
            return
        key = city_name.lower()
        if key not in self.cities:
            print(f"[infect_city] Ciudad desconocida: {city_name}")
            return
        city = self.cities[key]
        color = city.color
        # no infectar si la enfermedad está erradicada
        if self.eradicated.get(color, False):
            print(f"[INFECT] {city.name}: enfermedad {color} erradicada, no se coloca cubo.")
            return
        visited = set()
        for i in range(cubes):
            if city.infections < 3:
                city.infections += 1
                print(f"[INFECT] {city.name} recibió 1 cubo desde {source} (ahora {city.infections})")
            else:
                print(f"[INFECT] Intentando añadir 1 cubo a {city.name} (ya tiene 3) -> BROTE")
                self._outbreak_chain(key, visited)
            if self.outbreaks >= 8:
                self.game_over = True
                self.defeat_reason = "Max outbreaks reached (>=8)"
                print(f"[DERROTA] {self.defeat_reason}")
                return

    # ---------------------------
    # --- EPIDEMIC HANDLING ---
    # ---------------------------
    def _handle_epidemic(self):
        print("[EPIDEMIA] Se activó EPIDEMIA.")
        if self.infection_rate_index < len(self.infection_rate_list) - 1:
            self.infection_rate_index += 1
        print(f"  [EPIDEMIA] infection_rate_index -> {self.infection_rate_index} (rate = {self.infection_rate_list[self.infection_rate_index]})")
        # robar bottom carta del InfectionDeck
        try:
            bottom_card = self.infection_deck.draw_bottom()
        except IndexError:
            self.game_over = True
            self.defeat_reason = "InfectionDeck exhausted on epidemic (cannot draw bottom card)"
            print(f"[DERROTA] {self.defeat_reason}")
            return
        print(f"  [EPIDEMIA] Carta inferior robada: {bottom_card} -> infectar 3 cubos")
        # infectar con 3 cubos (permitir brotes en cadena)
        self.infect_city(bottom_card, cubes=3, source="epidemic")
        # descartar esa carta
        self.infection_deck.discard(bottom_card)
        # rebarajar descarte encima
        self.infection_deck.shuffle_discard_onto_deck_top()

    # ---------------------------
    # Jugadores y acciones
    # ---------------------------
    def add_player(self, player_name: str, start_city: str = "Atlanta"):
        key = start_city.lower()
        if key not in self.cities:
            raise ValueError(f"Ciudad de inicio desconocida: {start_city}")
        p = Player(player_name, self.cities[key].name)
        self.players.append(p)
        # repartir mano inicial: 2 cartas por jugador (estructura simplificada)
        try:
            for _ in range(2):
                card = self.player_deck.draw_card()
                p.hand.append(card)
        except IndexError:
            self.game_over = True
            self.defeat_reason = "PlayerDeck exhausted during initial deal"
            print(f"[DERROTA] {self.defeat_reason}")
        return p

    def _get_city(self, city_name: str) -> City:
        key = city_name.lower()
        if key not in self.cities:
            raise ValueError(f"Ciudad desconocida: {city_name}")
        return self.cities[key]

    # ---------------------------
    # Intercambio de cartas (Share Knowledge)
    # ---------------------------
    def share_knowledge(self, giver_index: int, receiver_index: int) -> bool:
        """
        El giver entrega al receiver la carta de la ciudad donde ambos están.
        Retorna True si intercambio realizado, False si inválido.
        """
        if self.game_over:
            print("[share_knowledge] Juego terminado.")
            return False
        if giver_index >= len(self.players) or receiver_index >= len(self.players):
            print("[share_knowledge] Índice de jugador inválido.")
            return False
        giver = self.players[giver_index]
        receiver = self.players[receiver_index]
        if giver.location != receiver.location:
            print("[share_knowledge] Ambos jugadores deben estar en la misma ciudad para compartir conocimiento.")
            return False
        city_name = giver.location
        # la carta de ciudad debe existir en la mano del giver (nombre exacto)
        # las cartas en mano usan nombre de ciudad o EVENT_/EPIDEMIC
        found = None
        for c in giver.hand:
            if c.lower() == city_name.lower():
                found = c
                break
        if not found:
            print(f"[share_knowledge] {giver.name} no tiene la carta de {city_name} para compartir.")
            return False
        # transferir
        if len(receiver.hand) >= Game.PLAYER_HAND_LIMIT:
            print(f"[share_knowledge] {receiver.name} tiene límite de mano ({Game.PLAYER_HAND_LIMIT}). Debe descartar antes de recibir.")
            # pedir al receptor descartar hasta 7 (interactivo)
            while len(receiver.hand) >= Game.PLAYER_HAND_LIMIT:
                print(f"Mano de {receiver.name}: {receiver.hand}")
                try:
                    choice = input(f"{receiver.name}, indica el número (1..{len(receiver.hand)}) de la carta a descartar: ").strip()
                    ix = int(choice) - 1
                    if 0 <= ix < len(receiver.hand):
                        discarded = receiver.hand.pop(ix)
                        self.player_deck.discard(discarded)
                        print(f"[share_knowledge] {receiver.name} descartó {discarded}.")
                    else:
                        print("Índice inválido.")
                except Exception:
                    print("Entrada inválida.")
        # ahora transferir
        giver.hand.remove(found)
        receiver.hand.append(found)
        print(f"[share_knowledge] {giver.name} entregó {found} a {receiver.name}.")
        return True

    # ---------------------------
    # Shuttle Flight (vuelo entre estaciones)
    # ---------------------------
    def shuttle(self, player_index: int, dest_city: str) -> bool:
        if self.game_over:
            print("[shuttle] Juego terminado.")
            return False
        if player_index >= len(self.players):
            print("[shuttle] Índice de jugador inválido.")
            return False
        player = self.players[player_index]
        if player.location not in self.research_stations:
            print("[shuttle] Debes estar en una estación de investigación para usar shuttle.")
            return False
        if dest_city not in self.research_stations:
            print("[shuttle] El destino debe tener estación de investigación.")
            return False
        origin = player.location
        player.move_to(dest_city)
        print(f"[ACCION] {player.name} viajó en vuelo de investigación de {origin} a {dest_city}.")
        return True

    # ---------------------------
    # Descubrir cura (actualiza erradicación)
    # ---------------------------
    def _check_and_set_eradication(self, color: str):
        if not self.cures_discovered.get(color, False):
            return
        if self.eradicated.get(color, False):
            return
        # si todas las ciudades de ese color tienen 0 cubos -> erradicada
        for c in self.cities.values():
            if c.color == color and c.infections > 0:
                return
        # si llegamos aquí -> erradicada
        self.eradicated[color] = True
        print(f"[ERRADICADA] La enfermedad {color} ha sido erradicada.")

    # ---------------------------
    # Robar cartas del PlayerDeck (manejo de EPIDEMIC y EVENT_X)
    # ---------------------------
    def _player_draw_card_to_hand(self, player: Player) -> bool:
        """Roba 1 carta y la añade a la mano del jugador; maneja EPIDEMIC si aparece.
           Retorna True si OK; False si derrota ocurrió."""
        try:
            card = self.player_deck.draw_card()
        except IndexError:
            self.game_over = True
            self.defeat_reason = "Sin cartas en PlayerDeck"
            print(f"[DERROTA] {self.defeat_reason}")
            return False

        # Mensajes para EVENT_X
        if card.startswith("EVENT"):
            print(f"[INFO] Se robó {card} (sin efecto en esta versión).")
            # mover a la mano y luego el jugador podrá descartarla (comportamiento simplificado)
            player.hand.append(card)
        elif card == "EPIDEMIC":
            print(f"[EPIDEMIA] Se robó EPIDEMIC del PlayerDeck.")
            self.player_deck.discard(card)
            self._handle_epidemic()
            if self.game_over:
                return False
            # EPIDEMIC no va a la mano
            return True
        else:
            print(f"[PlayerDeck] {player.name} robó: {card}")
            player.hand.append(card)

        # si supera límite, pedir descartes interactivos
        while len(player.hand) > Game.PLAYER_HAND_LIMIT:
            print(f"[EVENTO] {player.name} supera límite de mano ({len(player.hand)}). Debe descartar hasta {Game.PLAYER_HAND_LIMIT}.")
            for idx, h in enumerate(player.hand, 1):
                print(f"  {idx}. {h}")
            try:
                choice = input(f"{player.name}, indica el número de la carta a descartar: ").strip()
                ix = int(choice) - 1
                if 0 <= ix < len(player.hand):
                    discarded = player.hand.pop(ix)
                    self.player_deck.discard(discarded)
                    print(f"[EVENTO] {player.name} descartó {discarded}.")
                else:
                    print("Índice inválido. Intenta de nuevo.")
            except Exception:
                print("Entrada inválida. Intenta de nuevo.")
        return True

    def player_draw_n_cards(self, player_index: int = 0, n: int = 2) -> bool:
        if self.game_over:
            return False
        player = self.players[player_index]
        for _ in range(n):
            ok = self._player_draw_card_to_hand(player)
            if not ok:
                return False
        return True

    # ---------------------------
    # Fase de infección (respeta erradicación)
    # ---------------------------
    def infection_phase(self):
        if self.game_over:
            return
        rate = self.infection_rate_list[self.infection_rate_index]
        print(f"[Fase de infección] Robando {rate} carta(s) del InfectionDeck (rate index {self.infection_rate_index}).")
        for _ in range(rate):
            try:
                card = self.infection_deck.draw_top()
            except IndexError:
                self.game_over = True
                self.defeat_reason = "InfectionDeck exhausted during infection phase"
                print(f"[DERROTA] {self.defeat_reason}")
                return
            print(f"[InfectionDeck] Robada carta: {card}")
            # infectar respetando erradicación
            self.infect_city(card, cubes=1, source="infection_deck")
            self.infection_deck.discard(card)
            if self.game_over:
                return

    # ---------------------------
    # Flujo de turno completo integrado en Game (acciones, robos, infección)
    # ---------------------------
    def run_turn(self, actions: List[Tuple[str, Optional[str]]], player_index: int = 0):
        """
        Ejecuta un turno completo:
         - Hasta 4 acciones (cada action es una tupla (accion, param) )
         - Robar 2 cartas (maneja EPIDEMIC / EVENT)
         - Fase de infección
         - Check victory/defeat and eradication checks
        Acciones válidas:
         move <ciudad>, cure, build, discover_cure, share <receiver_name>, shuttle <dest_city>, skip
        """
        if self.game_over:
            print("[run_turn] Juego terminado; no se pueden jugar más turnos.")
            return

        if player_index != self.current_player_index:
            print(f"[run_turn] Aviso: player_index {player_index} != current_player_index {self.current_player_index}")

        player = self.players[player_index]
        actions_allowed = 4
        used = 0

        for act in actions:
            if used >= actions_allowed:
                break
            cmd = act[0].lower()
            param = act[1] if len(act) > 1 else None

            # mapear acciones con llamadas
            if cmd == "move":
                ok = self.perform_action(("move", param), player_index=player_index)
            elif cmd in ("cure", "treat"):
                ok = self.perform_action(("cure", None), player_index=player_index)
                # después de curar, verificar erradicación del color de la ciudad
                cur_city = self._get_city(player.location)
                self._check_and_set_eradication(cur_city.color)
            elif cmd == "build":
                ok = self.perform_action(("build", None), player_index=player_index)
            elif cmd == "discover_cure":
                ok = self.perform_action(("discover_cure", None), player_index=player_index)
                # tras descubrir cura, comprobar erradicación para cada color
                for color in ["Blue", "Yellow", "Black", "Red"]:
                    self._check_and_set_eradication(color)
            elif cmd == "share":
                # param: nombre receptor o índice
                if not param:
                    print("[run_turn] share requiere el nombre del receptor como parámetro.")
                    ok = False
                else:
                    # buscar índice por nombre (case-insensitive)
                    recv_idx = None
                    for i, pl in enumerate(self.players):
                        if pl.name.lower() == str(param).lower():
                            recv_idx = i
                            break
                    if recv_idx is None:
                        print(f"[run_turn] Jugador receptor {param} no encontrado.")
                        ok = False
                    else:
                        ok = self.share_knowledge(player_index, recv_idx)
            elif cmd == "shuttle":
                if not param:
                    print("[run_turn] shuttle requiere ciudad destino como parámetro.")
                    ok = False
                else:
                    ok = self.shuttle(player_index, param)
            elif cmd == "skip":
                ok = True
                print(f"[ACCION] {player.name} saltó una acción.")
            else:
                print(f"[run_turn] Acción desconocida: {cmd}")
                ok = False

            if ok:
                used += 1
            if self.game_over:
                return

        if used < actions_allowed:
            remaining = actions_allowed - used
            print(f"[run_turn] Quedan {remaining} acción(es) que serán 'skip' automáticamente.")

        # 1) Robar 2 cartas del PlayerDeck (manejar EPIDEMIC/EVENT)
        if not self.player_draw_n_cards(player_index=player_index, n=2):
            return

        # 2) Fase de infección
        self.infection_phase()
        if self.game_over:
            return

        # 3) Check eradication for all colors (in case infections were removed)
        for color in ["Blue", "Yellow", "Black", "Red"]:
            self._check_and_set_eradication(color)

        # 4) Check victory: all cures discovered
        if all(self.cures_discovered.values()):
            self.game_over = True
            print("[VICTORIA] ¡Se descubrieron las 4 curas! Has ganado el juego.")
            return

        # 5) Advance turn
        self.turn += 1
        if len(self.players) > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)

        # 6) Summary line
        hand_sizes = [len(p.hand) for p in self.players]
        print(f"Turno {self.turn-1} — Brotes: {self.outbreaks} — Curas: {self.cures_discovered} — Centros: {len(self.research_stations)} — Cartas jugadores: {hand_sizes}")

    # ---------------------------
    # Acciones básicas ya implementadas en v0.3
    # ---------------------------
    def perform_action(self, action: Tuple[str, Optional[str]], player_index: int = 0) -> bool:
        """
        Mantiene acciones básicas: move, cure, build, discover_cure, skip.
        Las acciones 'share' y 'shuttle' se manejan en run_turn para poder pasar parámetros más fácilmente.
        """
        if self.game_over:
            print("[perform_action] Juego terminado.")
            return False
        if player_index >= len(self.players):
            print("[perform_action] Índice de jugador inválido.")
            return False
        player = self.players[player_index]
        act = action[0].lower()
        param = action[1] if len(action) > 1 else None

        if act == "move":
            if not param:
                print("[perform_action] 'move' requiere ciudad destino.")
                return False
            try:
                dest = self._get_city(param)
            except ValueError:
                print(f"[perform_action] Ciudad destino desconocida: {param}")
                return False
            src = self._get_city(player.location)
            if dest.name not in src.neighbors:
                print(f"[perform_action] Movimiento inválido: {src.name} no está conectado con {dest.name}.")
                return False
            player.move_to(dest.name)
            print(f"[ACCION] {player.name} se movió de {src.name} a {dest.name}.")
            return True

        elif act in ("cure", "treat"):
            city = self._get_city(player.location)
            color = city.color
            if self.cures_discovered.get(color, False):
                removed = city.infections
                city.infections = 0
                print(f"[CURA] {player.name} curó {city.name} completamente (cura descubierta) -> removidos {removed} cubos.")
            else:
                if city.infections > 0:
                    city.infections -= 1
                    print(f"[ACCION] {player.name} trató {city.name}, -1 cubo (ahora {city.infections}).")
                else:
                    print(f"[ACCION] {player.name} intentó tratar {city.name} pero no había cubos.")
            # verificar erradicación para ese color
            self._check_and_set_eradication(color)
            return True

        elif act == "build":
            city = self._get_city(player.location)
            if city.name in self.research_stations:
                print(f"[ACCION] Ya existe estación en {city.name}.")
                return False
            if len(self.research_stations) >= Game.MAX_RESEARCH_STATIONS:
                print(f"[ACCION] No se pueden construir más estaciones (máx {Game.MAX_RESEARCH_STATIONS}).")
                return False
            self.research_stations.append(city.name)
            print(f"[ACCION] {player.name} construyó Estación de Investigación en {city.name}. Total estaciones: {len(self.research_stations)}")
            return True

        elif act == "discover_cure":
            city = self._get_city(player.location)
            if city.name not in self.research_stations:
                print("[ACCION] Debes estar en una estación de investigación para descubrir cura.")
                return False
            # contar cartas de cada color en la mano del jugador (solo cartas de ciudad cuentan)
            color_counts: Dict[str, List[str]] = {"Blue": [], "Yellow": [], "Black": [], "Red": []}
            for card in player.hand:
                if card.startswith("EVENT") or card == "EPIDEMIC":
                    continue
                key = card.lower()
                if key in self.cities:
                    c = self.cities[key]
                    color_counts[c.color].append(card)
            for col, cards in color_counts.items():
                if len(cards) >= 5 and not self.cures_discovered[col]:
                    to_use = cards[:5]
                    for cc in to_use:
                        player.hand.remove(cc)
                        self.player_deck.discard(cc)
                    self.cures_discovered[col] = True
                    print(f"[CURA] ¡Cura descubierta para la enfermedad {col}!")
                    # tras descubrir cura, verificar erradicación inmediatamente
                    self._check_and_set_eradication(col)
                    # comprobar victoria
                    if all(self.cures_discovered.values()):
                        self.game_over = True
                        print("[VICTORIA] ¡Se descubrieron las 4 curas! Has ganado el juego.")
                    return True
            print("[ACCION] No hay 5 cartas del mismo color en la mano para descubrir cura.")
            return False

        elif act == "skip":
            print(f"[ACCION] {player.name} saltó una acción.")
            return True

        else:
            print(f"[perform_action] Acción desconocida: {act}")
            return False

    # ---------------------------
    # Utilidades / diagnóstico
    # ---------------------------
    def show_status(self):
        print("\n=== Estado del juego (v0.4) ===")
        print(f"Turno: {self.turn}")
        cur_player = self.players[self.current_player_index].name if self.players else "N/A"
        print(f"Jugador actual: {self.current_player_index} ({cur_player})")
        print(f"Infection rate index: {self.infection_rate_index} -> {self.infection_rate_list[self.infection_rate_index]}")
        print(f"Outbreaks: {self.outbreaks}")
        print(f"Research stations ({len(self.research_stations)}/{Game.MAX_RESEARCH_STATIONS}): {self.research_stations}")
        print(f"Cures discovered: {self.cures_discovered}")
        print(f"Eradicated: {self.eradicated}")
        print(f"InfectionDeck: {self.infection_deck.status()} | PlayerDeck: {self.player_deck.status()}")
        for key in sorted(self.cities.keys()):
            c = self.cities[key]
            print(f" - {c.name:20} | {c.color:6} | inf: {c.infections}")
        print("Jugadores y manos:")
        for p in self.players:
            print(f" - {p.name} en {p.location} | mano({len(p.hand)}): {p.hand}")
        if self.game_over:
            print(f"*** JUEGO TERMINADO: {self.defeat_reason or 'Victoria'} ***")
        print("================================\n")

    # conveniencias
    def quick_move(self, dest_city_name: str, player_index: int = 0):
        return self.perform_action(("move", dest_city_name), player_index=player_index)

    def quick_cure(self, player_index: int = 0):
        return self.perform_action(("cure", None), player_index=player_index)


# ---------------------------
# Interfaz de consola integrada (runner)
# ---------------------------
def main():
    print("=== PANDEMIC v0.4 ===")
    g = Game(seed=42)
    name = input("Nombre del primer jugador: ").strip()
    g.add_player(name, start_city="Atlanta")

    more = input("¿Agregar otro jugador? (s/n): ").strip().lower()
    while more == "s":
        n = input("Nombre del jugador: ").strip()
        # alternar ciudades de inicio sencillas
        start = "Atlanta"
        #start = "Chicago" if len(g.players) == 1 else "Atlanta"
        g.add_player(n, start_city=start)
        more = input("¿Agregar otro jugador? (s/n): ").strip().lower()

    print("\nJuego iniciado. Comandos: move <ciudad> / cure / build / discover_cure / share <jugador> / shuttle <ciudad> / skip / status / conexiones <ciudad> / fin")
    while not g.game_over:
        player = g.players[g.current_player_index]
        city_obj = g._get_city(player.location)
        print(f"\n=== Turno {g.turn} — {player.name} ===")
        print(f"Ubicación: {player.location} ({city_obj.color}) — infecciones: {city_obj.infections}")
        print(f"Estaciones: {g.research_stations} | Brotes: {g.outbreaks} | Curas: {g.cures_discovered} | Erradicadas: {g.eradicated}")
        print(f"Mano ({len(player.hand)}): {player.hand}")
        print("Conexiones:", ", ".join(city_obj.neighbors))

        actions: List[Tuple[str, Optional[str]]] = []
        while len(actions) < 4:
            cmd = input(f"Acción {len(actions)+1}/4 > ").strip()
            if cmd.lower() in ("fin", "end"):
                break
            if cmd.lower().startswith("move "):
                dest = cmd.split(" ", 1)[1].strip().title()
                actions.append(("move", dest))
            elif cmd.lower() in ("cure", "treat"):
                actions.append(("cure", None))
            elif cmd.lower() == "build":
                actions.append(("build", None))
            elif cmd.lower() == "discover_cure":
                actions.append(("discover_cure", None))
            elif cmd.lower().startswith("share "):
                rec = cmd.split(" ", 1)[1].strip()
                actions.append(("share", rec))
            elif cmd.lower().startswith("shuttle "):
                dest = cmd.split(" ", 1)[1].strip().title()
                actions.append(("shuttle", dest))
            elif cmd.lower() == "skip":
                actions.append(("skip", None))
            elif cmd.lower().startswith("conexiones "):
                base = cmd.split(" ", 1)[1].strip().title()
                base_key = base.lower()
                if base_key in g.cities:
                    print(f"{base} conecta con: {', '.join(g.cities[base_key].neighbors)}")
                else:
                    print("Esa ciudad no existe en el mapa.")
            elif cmd.lower() == "status":
                g.show_status()
            else:
                print("Comando no reconocido.")
        if not actions:
            print("No se planificaron acciones: se saltan 4 acciones.")
        else:
            print("\n[Resumen acciones]")
            for i, (a, p) in enumerate(actions, 1):
                print(f" {i}. {a} {p if p else ''}")
            ok = input("¿Ejecutar? (s/n): ").strip().lower()
            if ok != "s":
                print("Turno cancelado. No se ejecutarán acciones.")
                continue

        # Ejecutar turno
        g.run_turn(actions, player_index=g.current_player_index)
        g.show_status()
        if g.game_over:
            break
        cont = input("Continuar al siguiente turno? (s/n): ").strip().lower()
        if cont != "s":
            print("Saliendo del juego.")
            g.defeat_reason = "Juego finalizado por el usuario"
            break

    print(f"\nFIN DEL JUEGO. Razón: {g.defeat_reason or 'Victoria'}")


if __name__ == "__main__":
    main()
