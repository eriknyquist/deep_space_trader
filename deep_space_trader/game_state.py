import random

from deep_space_trader.planet import Planet
from deep_space_trader.items import ItemCollection
from deep_space_trader import constants as const


class State(object):
    def __init__(self):
        self.initialize()

    def initialize(self):
        self.planets = []
        self.money = const.INITIAL_MONEY
        self.travel_cost = const.INITIAL_TRAVEL_COST
        self.capacity = const.INITIAL_ITEM_CAPACITY
        self.items = ItemCollection()
        self.warehouse = ItemCollection()
        self.warehouse_gets_per_day = const.WAREHOUSE_GETS_PER_DAY
        self.warehouse_puts_per_day = const.WAREHOUSE_PUTS_PER_DAY
        self.planet_discovery_range = const.PLANET_DISCOVERY_RANGE
        self.max_store_purchases_per_day = const.MAX_STORE_PURCHASES_PER_DAY
        self.max_days = const.INITIAL_MAX_DAYS
        self.store_purchases = 0
        self.planets_discovered = 0
        self.day = 1
        self.level = 1

        self.warehouse_puts = 0
        self.warehouse_gets = 0
        self.expand_planets(const.INITIAL_PLANET_COUNT)
        self.current_planet = self.planets[0]
        self.current_planet.visited = True
        self.previous_planet = None


    def change_current_planet(self, planetname):
        for p in self.planets:
            if p.full_name == planetname:
                self.previous_planet = self.current_planet
                self.current_planet = p
                self.current_planet.visited = True
                return

    def next_day(self):
        if self.day == self.max_days:
            return False

        # Update prices of all items on all discovered planets
        for planet in self.planets:
            planet.clear_samples_today()
            for item in planet.items.iter_items():
                item.update_value()

        self.day += 1
        self.warehouse_puts = 0
        self.warehouse_gets = 0
        self.store_purchases = 0
        return True

    def expand_planets(self, num_new=None):
        if num_new is None:
            num_new = random.randrange(1, 10)

        new_planets = Planet.random(num=num_new)
        for new in new_planets:
            new.discovery_day = self.day
            new.items = ItemCollection.random(value_multiplier=self.level,
                                              quantity_multiplier=self.level)

        self.planets += new_planets
        self.planets_discovered += num_new
