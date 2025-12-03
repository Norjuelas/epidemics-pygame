# pandemic_v0_1_1.py
import random
from typing import Dict, List, Optional

class City:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # 'Blue', 'Yellow', 'Black', 'Red'
        self.infections = 0  # 0..3
        self.neighbors: List[str] = []

    def add_neighbor(self, other_city_name: str):
        if other_city_name not in self.neighbors:
            self.neighbors.append(other_city_name)

    def infect(self, n: int = 1):
        before = self.infections
        self.infections = min(3, self.infections + n)
        return self.infections - before

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


class Game:
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.cities: Dict[str, City] = {}
        self.players: List[Player] = []
        self.current_player_index = 0
        self.infection_rate = 2
        self.turn = 1
        self._setup_full_map()
        self._initial_infections()

    def _add_city(self, name: str, color: str):
        self.cities[name.lower()] = City(name, color)

    def _connect(self, a: str, b: str):
        a_key, b_key = a.lower(), b.lower()
        if a_key not in self.cities or b_key not in self.cities:
            raise ValueError(f"Intentando conectar ciudades desconocidas: {a} - {b}")
        self.cities[a_key].add_neighbor(self.cities[b_key].name)
        self.cities[b_key].add_neighbor(self.cities[a_key].name)

    def _setup_full_map(self):
        """Configura las 48 ciudades oficiales con colores y conexiones (bidireccional)."""
        # Añadir todas las ciudades con su color
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

        # Definir conexiones según el dataset proporcionado
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

        # Primero aseguramos que todas las ciudades de 'connections' existen (ya añadidas arriba).
        # Luego conectamos bidireccionalmente usando _connect.
        for city_name, neighs in connections:
            for nb in neighs:
                # _connect manejará duplicados si se llama varias veces
                try:
                    self._connect(city_name, nb)
                except ValueError as e:
                    # Esto no debería suceder si todos los nombres están correctamente añadidos,
                    # pero mejor informar (no romperá la inicialización).
                    print(f"[Warning] al conectar {city_name} con {nb}: {e}")

    def _initial_infections(self):
        """Coloca infecciones iniciales aleatorias para poder probar (sin brotes)."""
        cities_keys = list(self.cities.keys())
        sample = random.sample(cities_keys, k=4)
        for k in sample:
            self.cities[k].infect(random.choice([1, 2]))

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
        self.end_turn()

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
        self.end_turn()

    def show_status(self):
        print("\n=== Estado del juego ===")
        print(f"Turno: {self.turn}, Jugadores: {len(self.players)}, Tasa infección (simulada): {self.infection_rate}")
        print("Ciudades:")
        for key in sorted(self.cities.keys()):
            c = self.cities[key]
            neigh = ", ".join(c.neighbors)
            print(f" - {c.name:20} | color: {c.color:6} | inf: {c.infections} | neighbors: {neigh}")
        print("Jugadores:")
        for p in self.players:
            print(f" - {p.name} en {p.location}")
        print("=======================\n")

    def _infect_random_cities(self):
        keys = list(self.cities.keys())
        for _ in range(self.infection_rate):
            city_key = random.choice(keys)
            city = self.cities[city_key]
            added = city.infect(1)
            print(f"[Infección automática] {city.name} recibe {added} cubo(s) (ahora {city.infections}).")

    def end_turn(self):
        print(f"[Fin de turno] Procesando infecciones automáticas (turno {self.turn})...")
        self._infect_random_cities()
        self.turn += 1
        if len(self.players) > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print("[Fin de turno] Turno finalizado.\n")

    # Métodos de conveniencia
    def quick_move(self, dest_city_name: str, player_index: int = 0):
        player = self.players[player_index]
        self.move(player.location, dest_city_name, player_index=player_index)

    def quick_cure(self, player_index: int = 0):
        self.cure(player_index=player_index)
