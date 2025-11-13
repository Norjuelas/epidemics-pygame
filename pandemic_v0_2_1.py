# pandemic_v0_2_1.py
"""
Pandemic v0.2.1 (consola) - Implementación:
 - Brotes en cadena (regla oficial) con control de ciudades ya explotadas en la misma cadena.
 - InfectionDeck y PlayerDeck completos.
 - Manejo de Epidemic (aumenta infection rate index, roba carta inferior de InfectionDeck, infecta 3 cubos,
   baraja descarte y lo coloca encima del mazo).
 - Turno con 4 acciones exactas, opción 'skip' por acción, luego robar 2 cartas y fase de infección.
 - Condiciones de derrota: no poder robar PlayerDeck o InfectionDeck.
 - Impresiones para depuración.
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

    def move_to(self, city_name: str):
        self.location = city_name

    def __repr__(self):
        return f"Player({self.name} @ {self.location})"


# ---------------------------
# InfectionDeck
# ---------------------------
class InfectionDeck:
    def __init__(self, cities: List[str]):
        """
        deck: top is at index 0 (pop(0) to draw top)
        bottom card is at the end (pop() to draw bottom)
        """
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
        return self.deck.pop()  # bottom = end

    def discard(self, card: str):
        self.discard_pile.append(card)

    def shuffle_discard_onto_deck_top(self):
        """
        Baraja el descarte y lo coloca encima del mazo (las cartas barajadas se colocan en la parte superior).
        """
        if not self.discard_pile:
            return
        print("[InfectionDeck] Barajando descarte y colocándolo encima del mazo.")
        temp = list(self.discard_pile)
        random.shuffle(temp)
        # colocar las cartas mezcladas encima del mazo (es decir: temp + deck)
        self.deck = temp + self.deck
        self.discard_pile = []

    def status(self):
        return {"deck": len(self.deck), "discard": len(self.discard_pile)}


# ---------------------------
# PlayerDeck (con setup de epidemias)
# ---------------------------
class PlayerDeck:
    def __init__(self, cities: List[str], n_epidemics: int = 6, n_events: int = 5, seed: Optional[int] = None):
        """
        Setup estándar:
         - Todas las cartas de ciudad
         - n_events cartas de evento (placeholders)
         - n_epidemics cartas 'EPIDEMIC'
         - Mezclar y dividir en n_epidemics pilas, insertar 1 EPIDEMIC por pila, barajar cada pila,
           luego apilar las pilas para formar deck final.
        """
        if seed is not None:
            random.seed(seed)
        base = list(cities)
        # añadir eventos
        for i in range(1, n_events + 1):
            base.append(f"EVENT_{i}")
        # ahora dividimos en n_epidemics pilas lo más igual posible
        random.shuffle(base)
        piles: List[List[str]] = []
        pile_size = len(base) // n_epidemics
        remainder = len(base) % n_epidemics
        idx = 0
        for i in range(n_epidemics):
            size = pile_size + (1 if i < remainder else 0)
            piles.append(base[idx: idx + size])
            idx += size
        # añadir una EPIDEMIC a cada pila y barajar cada pila
        for i in range(n_epidemics):
            piles[i].append("EPIDEMIC")
            random.shuffle(piles[i])
        # apilar las pilas en orden (la primera pila quedará arriba del mazo final)
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
        """
        En reglas reales las cartas de jugador se rebarajan solo si es necesario (p.ej. eventos).
        Aquí proveyemos la función para futuro uso.
        """
        if not self.discard_pile:
            return
        temp = list(self.discard_pile)
        random.shuffle(temp)
        self.deck.extend(temp)
        self.discard_pile = []

    def status(self):
        return {"deck": len(self.deck), "discard": len(self.discard_pile)}


# ---------------------------
# Game v0.2.1
# ---------------------------
class Game:
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.cities: Dict[str, City] = {}
        self.players: List[Player] = []
        self.current_player_index = 0

        # Contadores globales
        self.infection_rate_list = [2, 2, 2, 3, 3, 4, 4]
        self.infection_rate_index = 0
        self.outbreaks = 0

        # Game state
        self.game_over = False
        self.defeat_reason: Optional[str] = None

        # Setup full map
        self._setup_full_map()

        # Decks
        city_names = [c.name for c in self.cities.values()]
        self.infection_deck = InfectionDeck(city_names)
        self.player_deck = PlayerDeck(city_names)

        # Inicializaciones
        self.turn = 1

        # Inicial infections: por simplicidad usamos el proceso oficial reducido:
        # normalmente se ponen 3,3,2,1 a varias ciudades; aquí colocamos 4 ciudades aleatorias 1-2 cubos
        self._initial_infections()

    # ---------------------------
    # Mapa (igual que v0.1.1)
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
        blue = [
            "San Francisco","Chicago","Atlanta","Montreal","New York","Washington",
            "London","Madrid","Paris","Essen","Milan","St. Petersburg"
        ]
        yellow = [
            "Los Angeles","Mexico City","Miami","Bogota","Lima","Santiago",
            "Buenos Aires","Sao Paulo","Lagos","Khartoum","Kinshasa","Johannesburg"
        ]
        black = [
            "Algiers","Istanbul","Moscow","Cairo","Baghdad","Tehran",
            "Karachi","Riyadh","Delhi","Mumbai","Chennai","Kolkata"
        ]
        red = [
            "Bangkok","Jakarta","Ho Chi Minh City","Hong Kong","Shanghai","Beijing",
            "Seoul","Tokyo","Osaka","Taipei","Manila","Sydney"
        ]

        for name in blue:
            self._add_city(name, "Blue")
        for name in yellow:
            self._add_city(name, "Yellow")
        for name in black:
            self._add_city(name, "Black")
        for name in red:
            self._add_city(name, "Red")

        connections = [
            # BLUE
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

            # YELLOW
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

            # BLACK
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

            # RED
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
                except ValueError as e:
                    print(f"[Warning] al conectar {city_name} con {nb}: {e}")

    # ---------------------------
    # Inicializaciones
    # ---------------------------
    def _initial_infections(self):
        cities_keys = list(self.cities.keys())
        sample = random.sample(cities_keys, k=4)
        for k in sample:
            city = self.cities[k]
            # ponemos 1-2 cubos iniciales (sin brotes)
            add = random.choice([1, 2])
            city.infections = min(3, city.infections + add)
            print(f"[Init] {city.name} inicial recibe {add} cubo(s) (ahora {city.infections}).")

    # ---------------------------
    # --- OUTBREAK CHAIN ---
    # ---------------------------
    def _outbreak_chain(self, city_key: str, visited: set):
        """
        Realiza un brote en city_key (ya confirmado que la ciudad tenía 3 y necesita estallar).
        visited: conjunto de keys que ya explotaron en esta cadena.
        """
        if city_key in visited:
            # ya explotó en esta cadena: nada que hacer
            return
        visited.add(city_key)
        city = self.cities[city_key]
        self.outbreaks += 1
        print(f"[BROTE] {city.name} estalla! Outbreaks = {self.outbreaks}")

        # propagar a vecinos
        for nb_name in city.neighbors:
            nb_key = nb_name.lower()
            nb_city = self.cities[nb_key]
            # si vecino tiene menos de 3, añadir 1 cubo
            if nb_city.infections < 3:
                nb_city.infections += 1
                print(f"  [BROTE->INFECT] {nb_city.name} recibe 1 cubo (ahora {nb_city.infections})")
            else:
                # vecino ya en 3 -> causa brote en cadena si no ha explotado ya en esta cadena
                if nb_key not in visited:
                    print(f"  [BROTE->CHAIN] {nb_city.name} también estalla (cadena).")
                    self._outbreak_chain(nb_key, visited)
                else:
                    print(f"  [BROTE->CHAIN] {nb_city.name} ya explotó en esta cadena: no repetir.")

    # ---------------------------
    # Manejo de infecciones (general)
    # ---------------------------
    def infect_city(self, city_name: str, cubes: int = 1, source: str = "generic"):
        """
        Infecta city_name con 'cubes' cubos. Permite brotes en cadena.
        - Crea una 'visited' set para la cadena de brotes por cada llamada de alto nivel.
        - Añade cubos uno a uno usando la misma visited set para permitir cascada correcta.
        """
        if self.game_over:
            print("[infect_city] Juego terminado; no se aplican infecciones.")
            return

        key = city_name.lower()
        if key not in self.cities:
            print(f"[infect_city] Ciudad desconocida: {city_name}")
            return

        visited = set()
        for i in range(cubes):
            city = self.cities[key]
            if city.infections < 3:
                city.infections += 1
                print(f"[INFECT] {city.name} recibió 1 cubo desde {source} (ahora {city.infections})")
            else:
                # ciudad en 3 -> brote (inicia cadena si corresponde)
                print(f"[INFECT] Intentando añadir 1 cubo a {city.name} (ya tiene 3) -> BROTE")
                self._outbreak_chain(key, visited)

            # tras cada adición/brote verificamos si superamos límite de brotes
            if self.outbreaks >= 8:
                self.game_over = True
                self.defeat_reason = "Max outbreaks reached (>=8)"
                print(f"[GAMEOVER] {self.defeat_reason}")
                return

    # ---------------------------
    # --- EPIDEMIC HANDLING ---
    # ---------------------------
    def _handle_epidemic(self):
        """
        Procedimiento al sacar carta EPIDEMIC desde PlayerDeck:
         1) infection_rate_index += 1 (sube la tasa)
         2) robar carta BOTTOM del InfectionDeck -> infectarla con 3 cubos (permitiendo brotes)
         3) mover esa carta al discard de InfectionDeck
         4) barajar discard y ponerlo encima del deck (shuffle_discard_onto_deck_top)
        """
        print("[EPIDEMIC] ¡EPIDEMIA! Aplicando efectos de Epidemic...")
        # 1)
        if self.infection_rate_index < len(self.infection_rate_list) - 1:
            self.infection_rate_index += 1
            print(f"  [EPIDEMIC] Infection rate index aumenta a {self.infection_rate_index} (rate = {self.infection_rate_list[self.infection_rate_index]})")
        else:
            # si ya estamos en el tope, lo dejamos en el máximo índice
            self.infection_rate_index = len(self.infection_rate_list) - 1
            print(f"  [EPIDEMIC] Infection rate index ya está en tope ({self.infection_rate_index}).")

        # 2) robar BOTTOM del InfectionDeck
        try:
            bottom_card = self.infection_deck.draw_bottom()
        except IndexError:
            # no hay cartas -> derrota
            self.game_over = True
            self.defeat_reason = "InfectionDeck exhausted on epidemic (cannot draw bottom card)"
            print(f"[GAMEOVER] {self.defeat_reason}")
            return
        print(f"  [EPIDEMIC] Carta inferior robada: {bottom_card} -> recibe 3 cubos (posible brote).")

        # 3) infectar esa ciudad con 3 cubos (permitiendo brotes)
        self.infect_city(bottom_card, cubes=3, source="epidemic")

        # 4) mover esa carta al discard del InfectionDeck
        self.infection_deck.discard(bottom_card)
        # 5) barajar descarte y colocarlo encima
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
        return p

    def _get_city(self, city_name: str) -> City:
        key = city_name.lower()
        if key not in self.cities:
            raise ValueError(f"Ciudad desconocida: {city_name}")
        return self.cities[key]

    def perform_action(self, action: Tuple[str, Optional[str]], player_index: int = 0) -> bool:
        """
        Ejecuta una acción del jugador.
        action: tupla (action_name, param)
          - ("move", dest_city_name)
          - ("cure", None) => cura ciudad actual (1 cubo)
          - ("skip", None) => consume acción sin hacer nada
        Retorna True si acción válida / consumida, False si inválida (no consumir acción).
        """
        if self.game_over:
            print("[perform_action] Juego terminado; no se pueden realizar acciones.")
            return False

        if player_index >= len(self.players):
            print("[perform_action] Índice de jugador inválido.")
            return False

        player = self.players[player_index]
        act = action[0].lower()
        param = action[1] if len(action) > 1 else None

        if act == "move":
            if not param:
                print("[perform_action] 'move' requiere nombre de ciudad destino.")
                return False
            src = self._get_city(player.location)
            dest_name = param
            try:
                dest = self._get_city(dest_name)
            except ValueError:
                print(f"[perform_action] Ciudad destino desconocida: {dest_name}")
                return False
            if dest.name not in src.neighbors:
                print(f"[perform_action] Movimiento inválido: {src.name} no está conectado con {dest.name}.")
                return False
            player.move_to(dest.name)
            print(f"[Acción] {player.name} se movió de {src.name} a {dest.name}.")
            return True

        elif act == "cure" or act == "treat":
            city = self._get_city(player.location)
            if city.infections > 0:
                city.infections -= 1
                print(f"[Acción] {player.name} trató {city.name}, removiendo 1 cubo (ahora {city.infections}).")
            else:
                print(f"[Acción] {player.name} intentó tratar {city.name} pero no había cubos.")
            return True

        elif act == "skip":
            print(f"[Acción] {player.name} pasó una acción (skip).")
            return True

        else:
            print(f"[perform_action] Acción desconocida: {act}")
            return False

    # ---------------------------
    # Robar cartas del PlayerDeck (manejo de EPIDEMIC)
    # ---------------------------
    def player_draw_n_cards(self, player_index: int = 0, n: int = 2):
        """
        Roba n cartas para el jugador actual.
        Si aparece 'EPIDEMIC', se aplica _handle_epidemic() y la carta EPIDEMIC se descarta.
        Retorna True si todo OK, False si ocurrió derrota (PlayerDeck vacío).
        """
        if self.game_over:
            return False
        for i in range(n):
            try:
                card = self.player_deck.draw_card()
            except IndexError:
                self.game_over = True
                self.defeat_reason = "PlayerDeck exhausted (cannot draw player card)"
                print(f"[GAMEOVER] {self.defeat_reason}")
                return False
            print(f"[PlayerDeck] Robada carta del jugador: {card}")
            if card == "EPIDEMIC":
                # descartamos la epid card en player discard (regla: EPIDEMIC se va al descarte)
                self.player_deck.discard(card)
                # manejamos epid
                self._handle_epidemic()
                if self.game_over:
                    return False
            else:
                # para eventos y ciudades: por ahora las movemos al discard (estructura)
                # En futuras versiones eventos pueden activar efectos especiales
                self.player_deck.discard(card)
        return True

    # ---------------------------
    # Fase de infección
    # ---------------------------
    def infection_phase(self):
        if self.game_over:
            return
        rate = self.infection_rate_list[self.infection_rate_index]
        print(f"[Fase de infección] Robando {rate} cartas de InfectionDeck.")
        for _ in range(rate):
            try:
                card = self.infection_deck.draw_top()
            except IndexError:
                # no hay cartas -> derrota
                self.game_over = True
                self.defeat_reason = "InfectionDeck exhausted during infection phase"
                print(f"[GAMEOVER] {self.defeat_reason}")
                return
            print(f"[InfectionDeck] Robada carta: {card}")
            # infectar la ciudad con 1 cubo (permitiendo brotes en cadena)
            self.infect_city(card, cubes=1, source="infection_deck")
            # mover carta a discard
            self.infection_deck.discard(card)
            if self.game_over:
                return

    # ---------------------------
    # Flujo de turno: 4 acciones -> robar 2 cartas -> fase infección
    # ---------------------------
    def run_turn(self, actions: List[Tuple[str, Optional[str]]], player_index: int = 0):
        """
        Ejecuta un turno completo para player_index usando la lista de acciones provista.
        - actions: lista de hasta 4 acciones (tuplas). Si hay menos de 4, se pueden usar 'skip' implícitos.
        - cada acción válida consume una de las 4 acciones disponibles.
        """
        if self.game_over:
            print("[run_turn] Juego terminado; no se pueden jugar más turnos.")
            return

        if player_index != self.current_player_index:
            print(f"[run_turn] Advertencia: player_index {player_index} no coincide con current_player_index {self.current_player_index}.")

        actions_allowed = 4
        used_actions = 0

        for act in actions:
            if used_actions >= actions_allowed:
                break
            ok = self.perform_action(act, player_index=player_index)
            if ok:
                used_actions += 1
            # si la acción fue inválida (ok False) no consume la acción
            if self.game_over:
                return

        # si no se usaron las 4 acciones, las restantes se consideran 'skip' automáticamente
        if used_actions < actions_allowed:
            remaining = actions_allowed - used_actions
            print(f"[run_turn] {remaining} acción(es) restantes serán 'skip' automáticamente.")
            used_actions = actions_allowed

        # 1) Robar 2 cartas del PlayerDeck (puede activar EPIDEMIC)
        ok = self.player_draw_n_cards(player_index=player_index, n=2)
        if not ok:
            return

        # 2) Fase de infección
        self.infection_phase()
        if self.game_over:
            return

        # 3) Avanzar turno y jugador actual
        self.turn += 1
        if len(self.players) > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print(f"[run_turn] Turno completado. Ahora turno {self.turn}, current_player_index = {self.current_player_index}")

    # ---------------------------
    # Utilidades / diagnóstico
    # ---------------------------
    def show_status(self):
        print("\n=== Estado del juego (v0.2.1) ===")
        print(f"Turno: {self.turn}")
        print(f"Jugadores: {len(self.players)} (índice actual: {self.current_player_index})")
        current_rate = self.infection_rate_list[self.infection_rate_index]
        print(f"Infection rate index: {self.infection_rate_index} -> {current_rate}")
        print(f"Outbreaks: {self.outbreaks}")
        print(f"InfectionDeck: {self.infection_deck.status()} | PlayerDeck: {self.player_deck.status()}")
        print("Ciudades (nombre: color inf):")
        for key in sorted(self.cities.keys()):
            c = self.cities[key]
            print(f" - {c.name:20} | {c.color:6} | inf: {c.infections}")
        print("Jugadores:")
        for p in self.players:
            print(f" - {p.name} en {p.location}")
        if self.game_over:
            print(f"*** GAME OVER: {self.defeat_reason} ***")
        print("================================\n")

    def quick_move(self, dest_city_name: str, player_index: int = 0):
        player = self.players[player_index]
        return self.perform_action(("move", dest_city_name), player_index=player_index)

    def quick_cure(self, player_index: int = 0):
        return self.perform_action(("cure", None), player_index=player_index)
