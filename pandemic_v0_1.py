# pandemic_v0_1.py
import random
from typing import Dict, List, Optional

class City:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color  # p.ej. 'Blue', 'Yellow', 'Black', 'Red'
        self.infections = 0  # 0..3
        self.neighbors: List[str] = []  # almacenar nombres de ciudades

    def add_neighbor(self, other_city_name: str):
        if other_city_name not in self.neighbors:
            self.neighbors.append(other_city_name)

    def infect(self, n: int = 1):
        """Incrementa infecciones hasta un máximo de 3 (no implementamos brotes en v0.1)."""
        before = self.infections
        self.infections = min(3, self.infections + n)
        return self.infections - before  # cantidad realmente añadida

    def treat(self, n: int = 1):
        """Quita n cubos de infección (mínimo 0)."""
        before = self.infections
        self.infections = max(0, self.infections - n)
        return before - self.infections  # cantidad realmente removida

    def __repr__(self):
        return f"City({self.name}, {self.color}, inf={self.infections})"


class Player:
    def __init__(self, name: str, start_city: str):
        self.name = name
        self.location = start_city  # nombre de la ciudad

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
        self.infection_rate = 2  # infectaremos 2 ciudades al final del turno (simplificado)
        self.turn = 1
        self._setup_small_map()
        self._initial_infections()

    def _add_city(self, name: str, color: str):
        self.cities[name.lower()] = City(name, color)

    def _connect(self, a: str, b: str):
        a_key, b_key = a.lower(), b.lower()
        self.cities[a_key].add_neighbor(self.cities[b_key].name)
        self.cities[b_key].add_neighbor(self.cities[a_key].name)

    def _setup_small_map(self):
        """Mapa reducido con conexiones aproximadas del tablero original (para v0.1)."""
        # Añadir ciudades (nombre, color)
        city_list = [
            ("Atlanta", "Blue"), ("Washington", "Blue"), ("New York", "Blue"),
            ("Montreal", "Blue"), ("Chicago", "Blue"),
            ("San Francisco", "Blue"), ("Los Angeles", "Yellow"), ("Mexico City", "Yellow"),
            ("Miami", "Yellow"), ("Bogota", "Yellow"),
            ("London", "Blue"), ("Paris", "Blue")
        ]
        for name, color in city_list:
            self._add_city(name, color)

        # Conexiones (simplificadas)
        connections = [
            ("Atlanta", "Washington"), ("Atlanta", "Miami"), ("Atlanta", "Chicago"),
            ("Washington", "New York"), ("New York", "Montreal"), ("Chicago", "Montreal"),
            ("Chicago", "San Francisco"), ("San Francisco", "Los Angeles"), ("Los Angeles", "Mexico City"),
            ("Mexico City", "Miami"), ("Miami", "Bogota"), ("Bogota", "Mexico City"),
            ("London", "New York"), ("London", "Paris"), ("Paris", "Montreal"),
            ("Paris", "Chicago")
        ]
        for a, b in connections:
            self._connect(a, b)

    def _initial_infections(self):
        """Coloca algunas infecciones iniciales (aleatorias) para poder probar."""
        # Seleccionar 4 ciudades al azar y poner 1-2 cubos aleatorios (sin pasar de 3)
        cities_keys = list(self.cities.keys())
        sample = random.sample(cities_keys, k=4)
        for k in sample:
            added = self.cities[k].infect(random.choice([1, 2]))
            # no hacemos brotes en v0.1

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
        """Mover jugador si las ciudades están conectadas. Llama a end_turn() al finalizar la acción."""
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
        """Tratar la ciudad actual del jugador (o city_name si se da). Reduce 1 cubo."""
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
        # ordenar por nombre para legibilidad
        for key in sorted(self.cities.keys()):
            c = self.cities[key]
            neigh = ", ".join(c.neighbors)
            print(f" - {c.name:12} | color: {c.color:6} | inf: {c.infections} | neighbors: {neigh}")
        print("Jugadores:")
        for p in self.players:
            print(f" - {p.name} en {p.location}")
        print("=======================\n")

    def _infect_random_cities(self):
        """Infecta 'infection_rate' ciudades al azar (incrementando 1 cubo, sin brotes)."""
        keys = list(self.cities.keys())
        for _ in range(self.infection_rate):
            city_key = random.choice(keys)
            city = self.cities[city_key]
            added = city.infect(1)
            print(f"[Infección automática] {city.name} recibe {added} cubo(s) (ahora {city.infections}).")

    def end_turn(self):
        """Procesos al final del turno: infecciones automáticas y avance de turno."""
        print(f"[Fin de turno] Procesando infecciones automáticas (turno {self.turn})...")
        self._infect_random_cities()
        self.turn += 1
        # rotamos jugador actual (por si añadimos más jugadores luego)
        if len(self.players) > 0:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
        print("[Fin de turno] Turno finalizado.\n")

    # Métodos auxiliares para la consola
    def quick_move(self, dest_city_name: str, player_index: int = 0):
        """Mover desde la ciudad actual del jugador a dest_city_name (conveniencia)."""
        player = self.players[player_index]
        self.move(player.location, dest_city_name, player_index=player_index)

    def quick_cure(self, player_index: int = 0):
        """Tratar la ciudad donde está el jugador actual (conveniencia)."""
        self.cure(player_index=player_index)

