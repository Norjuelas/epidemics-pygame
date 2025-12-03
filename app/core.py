import random
from typing import List, Optional
from app.config import EVENT_NAMES

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

