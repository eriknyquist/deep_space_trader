import random
from collections import deque

from deep_space_trader.planet import Planet
from deep_space_trader.items import ItemCollection
from deep_space_trader import constants as const

# Ranges of possible health loss during battle, by battle level number
health_loss_ranges_by_battle_level = [
    (7, 10),  # battle level 0
    (7, 9),   # battle level 1
    (6, 9),   # battle level 2
    (5, 8),   # battle level 3
    (4, 7),   # battle level 4
    (4, 6),   # battle level 5
    (3, 5),   # battle level 6
    (2, 4),   # battle level 7
    (1, 3),   # battle level 8
    (0, 3),   # battle level 9
    (0, 2),   # battle level 10
]


class State(object):
    def __init__(self, main_widget):
        self.main_widget = main_widget
        self.initialize()

    def initialize(self):
        self.planets = []
        self.money = const.INITIAL_MONEY
        self.travel_cost = const.INITIAL_TRAVEL_COST
        self.capacity = const.INITIAL_ITEM_CAPACITY
        self.items = ItemCollection()
        self.warehouse = ItemCollection()
        self.warehouse_trips_per_day = const.WAREHOUSE_TRIPS_PER_DAY
        self.planet_discovery_range = const.PLANET_DISCOVERY_RANGE
        self.max_store_purchases_per_day = const.MAX_STORE_PURCHASES_PER_DAY
        self.max_days = const.INITIAL_MAX_DAYS
        self.store_purchases = 0
        self.planets_discovered = 0
        self.battle_level = 0
        self.max_battle_level = const.MAX_BATTLE_LEVEL
        self.scout_level = 0
        self.max_scout_level = const.MAX_SCOUT_LEVEL
        self.day = 1
        self.level = 1
        self.health = 100
        self.daily_cost = const.DAILY_LIVING_COST
        self.previous_planets = deque(maxlen=2)

        self.warehouse_trips = 0
        self.expand_planets(const.INITIAL_PLANET_COUNT)
        self.current_planet = self.planets[0]
        self.current_planet.visited = True
        self.previous_planet = None
        self.previous_planets_tail = None
        self.have_trading_console = False
        self.no_health_recovery = False

        self.travel_log = []
        self.transaction_log = []

        # Maps battle level to chance of winning battle by percentage.
        # Note: if const.MAX_BATTLE_LEVEL is changed, then this map might need to change too.
        self.battle_level_chance_map = {
            0: 1.0,
            1: 10.0,
            2: 15.0,
            3: 20.0,
            4: 25.0,
            5: 35.0,
            6: 50.0,
            7: 65.0,
            8: 80.0,
            9: 95.0,
            10: 99.0
        }

    def enable_trading_console(self):
        self.have_trading_console = True
        self.main_widget.locationBrowser.enableTradingConsole()

    def net_worth(self, include_warehouse=False):
        ret = self.items.total_value + self.money
        if include_warehouse:
            ret += self.warehouse.total_value

        return ret

    def chance_of_being_robbed_in_transit(self):
        value = self.net_worth()
        chance = 0.0

        if value > 100000000000:
            chance = 90.0
        elif value > 1000000000:
            chance = 80.0
        elif value > 500000000:
            chance = 60.0
        elif value > 50000000:
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

    def get_planet_by_name(self, planetname):
        for p in self.planets:
            if p.full_name == planetname:
                return p

        return None

    def change_current_planet(self, planetname):
        self.travel_log.append((planetname, self.day))

        if len(self.previous_planets) == self.previous_planets.maxlen:
            self.previous_planets_tail = self.previous_planets[-1]

        new_planet = self.get_planet_by_name(planetname)
        self.previous_planets.appendleft(self.current_planet)
        self.previous_planet = self.current_planet
        self.current_planet = new_planet
        self.current_planet.visited = True

    def record_sale(self, item_name, quantity, price):
        self.transaction_log.append(("sold", self.day, self.current_planet.full_name, item_name, quantity, price))

    def record_purchase(self, item_name, quantity, price):
        self.transaction_log.append(("bought", self.day, self.current_planet.full_name, item_name, quantity, price))

    def read_transaction_log(self):
        lines = []

        for desc, daynum, planetname, itemname, quantity, price in self.transaction_log:
            lines.append("Day %s: %s, %s %s %s for %s each" % (daynum, planetname, desc, quantity, itemname, price))

        return '\n'.join(lines)

    def read_travel_log(self):
        return '\n'.join("Day %s: %s" % (daynum, name) for name, daynum in self.travel_log)

    def next_day(self):
        if self.day == self.max_days:
            return False

        new_money = max(0, self.money - self.daily_cost)
        if (self.money == 0) and (new_money == 0):
            self.health = max(0, self.health - 15)
        else:
            if self.no_health_recovery:
                self.no_health_recovery = False
            else:
                self.health = min(100, self.health + 15)

        self.money = new_money
        self.day += 1
        self.warehouse_trips = 0
        self.store_purchases = 0
        return True

    def disable_health_recovery_today(self):
        self.no_health_recovery = True

    def lost_health_from_battle(self):
        # Randomly reduce health (higher battle level means less potential for loss)
        lower, upper = health_loss_ranges_by_battle_level[self.battle_level]
        health_loss = random.randrange(lower, upper)
        self.health = max(self.health - (health_loss * 10), 0)

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
