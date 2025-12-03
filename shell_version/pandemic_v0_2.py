# pandemic_v0_2.py
import random
from typing import Dict, List, Optional

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

    def infect_raw(self, n: int = 1):
        """Añade n cubos sin lógica de brotes (se usa para vecinos cuando no permitimos brotes en cadena)."""
        before = self.infections
        self.infections = min(3, self.infections + n)
        return self.infections - before

    def infect_with_outbreak_check(self, n: int = 1):
        """
        Añade n cubos y retorna:
         - added: cantidad realmente añadida (0..n)
         - outbreak: True si se intentó poner >3 (es decir, necesitaría brote)
        """
        before = self.infections
        target = before + n
        if target <= 3:
            self.infections = target
            return (self.infections - before, False)
        else:
            # no añadimos el cuarto cubo; indicamos que hay que hacer brote
            return (0, True)

    def treat(self, n: int = 1):
        before = self.infections
        self.infections = max(0, self.infections - n)
        return before - self.infections

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
    def __init__(self, cities: List[str], game_ref):
        """
        cities: lista de nombres de ciudad (48)
        game_ref: referencia al Game para aplicar infecciones (se usa para llamar a game.infect_city)
        """
        self.game = game_ref
        self.deck: List[str] = list(cities)
        self.discard_pile: List[str] = []
        random.shuffle(self.deck)

    def shuffle_discard_into_deck(self):
        if not self.discard_pile:
            return
        print("[InfectionDeck] Barajando descarte en el mazo de infección.")
        self.deck = self.discard_pile[::-1] + self.deck  # opcional: pone el descarte encima (estructura preparada)
        self.discard_pile = []
        random.shuffle(self.deck)

    def draw_card(self) -> str:
        if not self.deck:
            # En reglas reales, se baraja el descarte; aquí hacemos una remezcla simple
            print("[InfectionDeck] Mazo vacío — barajando descarte -> mazo.")
            self.shuffle_discard_into_deck()
            if not self.deck:
                raise RuntimeError("No hay cartas en InfectionDeck tras intentar rebarajar.")
        card = self.deck.pop(0)
        return card

    def discard(self, card: str):
        self.discard_pile.append(card)

    def infect(self, rate: int):
        """Roba 'rate' cartas e infecta esas ciudades (mueve cartas a descarte)."""
        print(f"[InfectionDeck] Infectando {rate} ciudad(es).")
        for _ in range(rate):
            card = self.draw_card()
            print(f"[InfectionDeck] Robada carta de infección: {card}")
            # Llamamos a game para infectar la ciudad (Game.infect_city maneja brotes)
            self.game.infect_city(card, source="infection_deck")
            # descartamos la carta
            self.discard(card)

    def status(self):
        return {"deck": len(self.deck), "discard": len(self.discard_pile)}


# ---------------------------
# PlayerDeck (estructura)
# ---------------------------
class PlayerDeck:
    def __init__(self, cities: List[str]):
        """
        deck: todas las cartas de ciudad + 5 eventos (placeholders) + 6 epidemias (placeholders)
        Esta clase sólo implementa estructura: draw_card, discard y estado.
        """
        self.deck: List[str] = list(cities)
        # añadir 5 eventos ficticios
        for i in range(1, 6):
            self.deck.append(f"EVENT_{i}")
        # añadir 6 cartas EPIDEMIC (sin activar aún)
        for i in range(1, 7):
            self.deck.append("EPIDEMIC")
        random.shuffle(self.deck)
        self.discard_pile: List[str] = []

    def draw_card(self) -> str:
        if not self.deck:
            raise RuntimeError("PlayerDeck vacío. En v0.2 aún no implementamos rebarajado de descartes.")
        return self.deck.pop(0)

    def discard(self, card: str):
        self.discard_pile.append(card)

    def status(self):
        return {"deck": len(self.deck), "discard": len(self.discard_pile)}


# ---------------------------
# Game (v0.2)
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

        # Setup del mapa completo
        self._setup_full_map()

        # Barajas
        all_city_names = [c.name for c in self.cities.values()]
        self.infection_deck = InfectionDeck(all_city_names, game_ref=self)
        self.player_deck = PlayerDeck(all_city_names)

        # Inicializaciones de juego
        self.turn = 1
        self._initial_infections()  # usa infection_deck? aquí aplicamos infecciones aleatorias simples

    # ---------------------------
    # Mapa (misma que v0.1.1)
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
        """Coloca 4 infecciones aleatorias (1-2 cubos) para probar."""
        cities_keys = list(self.cities.keys())
        sample = random.sample(cities_keys, k=4)
        for k in sample:
            added, _ = self.cities[k].infect_with_outbreak_check(random.choice([1, 2]))
            # notificar
            print(f"[Init] {self.cities[k].name} inicial recibe {added} cubo(s) ( ahora {self.cities[k].infections} ).")

    # ---------------------------
    # Manejo de infecciones y brotes
    # ---------------------------
    def infect_city(self, city_name: str, source: str = "generic"):
        """
        Intenta infectar 'city_name' con 1 cubo (por defecto).
        source: "infection_deck" o "player_action" etc (solo para logs).
        Reglas v0.2:
          - Si ciudad < 3: añade 1.
          - Si ciudad == 3 y se intenta añadir cuarto: se produce BROTE global (+1) y
            cada vecino recibe +1 cubo **sin** generar nuevos brotes en cadena (i.e., vecinos no explotan).
        """
        key = city_name.lower()
        if key not in self.cities:
            print(f"[infect_city] Ciudad desconocida: {city_name}")
            return

        city = self.cities[key]
        added, needs_outbreak = city.infect_with_outbreak_check(1)
        if needs_outbreak:
            # Brote
            self.outbreaks += 1
            print(f"[BROTE] En {city.name} (source={source})! Contador de brotes ahora: {self.outbreaks}")
            # Infectar a cada vecino pero SIN permitir que esos infecten generen más brotes
            for nb_name in city.neighbors:
                nb_key = nb_name.lower()
                nb_city = self.cities[nb_key]
                added_nb = nb_city.infect_raw(1)  # no genera brote aunque ya tenga 3
                if added_nb > 0:
                    print(f"  [BROTE->INFECT] {nb_city.name} recibe {added_nb} cubo(s) (ahora {nb_city.infections})")
                else:
                    # Si estaba en 3 ya, no se añade y no hay brote en cadena
                    print(f"  [BROTE->INFECT] {nb_city.name} ya tenía 3 cubos, no se añade (no hay brote en cadena).")
        else:
            if added > 0:
                print(f"[INFECT] {city.name} recibió {added} cubo(s) desde {source} (ahora {city.infections})")
            else:
                # no se añadió (caso raro)
                print(f"[INFECT] {city.name} no cambió (desde {source}).")

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

    def move(self, from_city: str, to_city: str, player_index: int = 0):
        if player_index >= len(self.players):
            raise IndexError("Índice de jugador inválido.")
        player = self.players[player_index]
        if player.location.lower() != from_city.lower():
            raise ValueError(f"El jugador {player.name} no está en {from_city} (está en {player.location}).")
        src = self._get_city(from_city)
        dest = self._get_city(to_city)
        if dest.name not in src.neighbors:
            raise ValueError(f"{src.name} no está conectado con {dest.name}. Movimiento inválido.")
        player.move_to(dest.name)
        print(f"[Acción] {player.name} se movió de {src.name} a {dest.name}.")
        # NOTA: no llamamos end_turn automáticamente — dejaremos al flujo llamar a end_turn() cuando corresponda
        # (en v0.1 se llamaba automáticamente; aquí preferimos control explícito)
        return True

    def cure(self, city_name: Optional[str] = None, player_index: int = 0):
        if player_index >= len(self.players):
            raise IndexError("Índice de jugador inválido.")
        player = self.players[player_index]
        target_name = city_name if city_name is not None else player.location
        city = self._get_city(target_name)
        removed = city.treat(1)
        if removed > 0:
            print(f"[Acción] {player.name} trató {city.name}, removiendo {removed} cubo(s). Ahora tiene {city.infections}.")
        else:
            print(f"[Acción] {player.name} trató {city.name}, pero no había cubos para remover.")
        return True

    # ---------------------------
    # Flujo de turno (v0.2)
    # ---------------------------
    def player_draw_cards(self, player_index: int = 0, n: int = 2):
        """Estructura: roba n cartas y las descarta (sin efectos implementados)."""
        print(f"[PlayerDeck] Jugador {self.players[player_index].name} roba {n} carta(s).")
        for i in range(n):
            try:
                card = self.player_deck.draw_card()
                print(f"  [PlayerDeck] Robada: {card}")
                # En v0.2 sólo estructura: pasamos a descarte inmediatamente (sin efectos)
                self.player_deck.discard(card)
            except RuntimeError as e:
                print(f"  [PlayerDeck] Error al robar carta: {e}")

    def infection_phase(self):
        """Fase de infección: robar infection_rate cartas e infectar."""
        rate = self.infection_rate_list[self.infection_rate_index]
        print(f"[Fase de infección] Tasa actual: {rate} (index {self.infection_rate_index})")
        self.infection_deck.infect(rate)

    def end_turn(self):
        """Termina turno: jugador roba cartas de jugador (estructura) y se ejecuta fase infección."""
        print(f"[Fin de turno] Procesando robo de cartas de jugador y fase de infección (Turno {self.turn})...")
        # 1) Robo de cartas de jugador (2 cartas por turno)
        if len(self.players) > 0:
            self.player_draw_cards(player_index=self.current_player_index, n=2)
        # 2) Fase de infección
        self.infection_phase()
        # 3) Avanzar turno y jugador actual
        self.turn += 1
        if len(self.players) > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        # 4) Comprobar condiciones de fin de juego
        if self.outbreaks >= 8:
            print("[GAMEOVER] Se alcanzaron 8 brotes. Juego terminado (derrota).")
        print("[Fin de turno] Finalizado.\n")

    # ---------------------------
    # Utilidades / diagnóstico
    # ---------------------------
    def show_status(self):
        print("\n=== Estado del juego (v0.2) ===")
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
        print("================================\n")

    def quick_move(self, dest_city_name: str, player_index: int = 0):
        player = self.players[player_index]
        return self.move(player.location, dest_city_name, player_index=player_index)

    def quick_cure(self, player_index: int = 0):
        return self.cure(player_index=player_index)
