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
        self.battle_level = 0
        self.max_battle_level = const.MAX_BATTLE_LEVEL
        self.scout_level = 1
        self.max_scout_level = const.MAX_SCOUT_LEVEL
        self.day = 1
        self.level = 1

        self.warehouse_puts = 0
        self.warehouse_gets = 0
        self.expand_planets(const.INITIAL_PLANET_COUNT)
        self.current_planet = self.planets[0]
        self.current_planet.visited = True
        self.previous_planet = None

        self.travel_log = []

        # Maps battle level to chance of winning battle by percentage.
        # Note: if const.MAX_BATTLE_LEVEL is changed, then this map might need to change too.
        self.battle_level_chance_map = {
            0: 0.0,
            1: 10.0,
            2: 15.0,
            3: 20.0,
            4: 25.0,
            5: 35.0,
            6: 50.0,
            7: 65.0,
            8: 80.0,
            9: 95.0,
            10: 100.0
        }

    def net_worth(self, include_warehouse=False):
        ret = self.items.total_value + self.money
        if include_warehouse:
            ret += self.warehouse.total_value

        return ret

    def chance_of_being_robbed_in_transit(self):
        value = self.net_worth()
        chance = 0.0

        if value > 1000000000000:
            chance = 90.0
        elif value > 500000000000:
            chance = 80.0
        elif value > 25000000000:
            chance = 60.0
        elif value > 100000000:
            chance = 30.0
        elif value > 10000000:
            chance = 15.0
        elif value > 1000000:
            chance = 5.0

        return chance

    def battle_victory_chance_percentage(self):
        return self.battle_level_chance_map[self.battle_level]

    def battle_won(self):
        win_chance_percent = self.battle_victory_chance_percentage()
        return random.randint(0, 100) <= win_chance_percent

    def change_current_planet(self, planetname):
        self.travel_log.append((planetname, self.day))

        for p in self.planets:
            if p.full_name == planetname:
                self.previous_planet = self.current_planet
                self.current_planet = p
                self.current_planet.visited = True
                return

    def read_travel_log(self):
        return '\n'.join("Day %s: %s" % (daynum, name) for name, daynum in self.travel_log)

    def next_day(self):
        if self.day == self.max_days:
            return False

        self.day += 1
        self.warehouse_puts = 0
        self.warehouse_gets = 0
        self.store_purchases = 0
        return True

    def update_planet_item_prices(self):
        # Update prices of all items on all discovered planets
        for planet in self.planets:
            planet.clear_samples_today()
            for item in planet.items.iter_items():
                item.update_value()

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
