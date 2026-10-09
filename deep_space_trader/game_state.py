import math
import random
from collections import deque

from deep_space_trader.planet import Planet
from deep_space_trader.items import ItemCollection
from deep_space_trader import constants as const
from deep_space_trader.utils import percentChance
from deep_space_trader.items import itemDisplayName
from deep_space_trader.i18n import translate, formatNumber

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
        self.engine_level = 0
        self.capacity = const.INITIAL_ITEM_CAPACITY
        self.items = ItemCollection()
        self.warehouse = ItemCollection()
        self.warehouse_trips_per_day = const.WAREHOUSE_TRIPS_PER_DAY
        self.planet_discovery_range = const.PLANET_DISCOVERY_RANGE
        self.max_store_purchases_per_day = const.MAX_STORE_PURCHASES_PER_DAY
        self.max_days = const.INITIAL_MAX_DAYS
        self.store_purchases = 0
        self.planets_discovered = 0
        self.battle_level = const.INITIAL_BATTLE_LEVEL
        self.max_battle_level = const.MAX_BATTLE_LEVEL
        self.scout_level = const.INITIAL_SCOUT_LEVEL
        self.max_scout_level = const.MAX_SCOUT_LEVEL
        self.day = 1
        self.level = 1
        self.health = 100
        self.daily_cost = const.DAILY_LIVING_COST
        self.previous_planets = deque(maxlen=2)

        # Full names of every planet generated this game, including destroyed
        # ones, so that no two planets ever share a name
        self.used_planet_names = set()

        self.warehouse_trips = 0
        self.expand_planets(const.INITIAL_PLANET_COUNT)

        # The first planet is home: the centre of the galaxy, where the warehouse is
        self.home_planet = self.planets[0]
        self.home_planet.x = 0.0
        self.home_planet.y = 0.0

        self.current_planet = self.home_planet
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
            2: 20.0,
            3: 30.0,
            4: 40.0,
            5: 50.0,
            6: 60.0,
            7: 70.0,
            8: 80.0,
            9: 90.0,
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

    def pirate_chance(self, planet):
        """
        Percentage chance of meeting pirates on the way to 'planet'. Grows with
        net worth (see chance_of_being_robbed_in_transit) and with trip distance
        """
        low, high = const.PIRATE_DISTANCE_FACTOR_RANGE
        distance = self.current_planet.distance_to(planet)
        factor = min(high, max(low, distance / const.PIRATE_REFERENCE_DISTANCE))
        return min(const.MAX_PIRATE_CHANCE_PERCENTAGE, self.chance_of_being_robbed_in_transit() * factor)

    def travel_cost_per_ly(self):
        return const.TRAVEL_COST_PER_LY * (const.ENGINE_TRAVEL_COST_FACTOR ** self.engine_level)

    def travel_cost_to(self, planet):
        """
        Cost of travelling from the current planet to 'planet'
        """
        distance = self.current_planet.distance_to(planet)
        return max(const.MIN_TRAVEL_COST, int(round(distance * self.travel_cost_per_ly())))

    def discovery_distances(self):
        """
        (smallest, largest) distance from the home planet for newly discovered planets
        """
        if self.scout_level == 0:
            # Only the starting planets are discovered without a scout fleet
            return 0.0, const.INITIAL_GALAXY_RADIUS

        return const.INITIAL_GALAXY_RADIUS, const.INITIAL_GALAXY_RADIUS * (self.scout_level + 1)

    @staticmethod
    def remote_price_factor(distance):
        """
        How much cheaper items are on a planet this far from home: 1.0 (normal
        prices) out to INITIAL_GALAXY_RADIUS, falling steadily to
        REMOTE_PRICE_FACTOR at the edge of the largest scout range
        """
        inner = const.INITIAL_GALAXY_RADIUS
        outer = const.INITIAL_GALAXY_RADIUS * (const.MAX_SCOUT_LEVEL + 1)
        progress = min(1.0, max(0.0, (distance - inner) / (outer - inner)))
        return 1.0 - progress * (1.0 - const.REMOTE_PRICE_FACTOR)

    def battle_victory_chance_percentage(self):
        return self.battle_level_chance_map[self.battle_level]

    def battle_won(self):
        win_chance_percent = self.battle_victory_chance_percentage()
        return percentChance(win_chance_percent)

    def change_current_planet(self, new_planet):
        self.travel_log.append((new_planet.full_name, self.day))

        if len(self.previous_planets) == self.previous_planets.maxlen:
            self.previous_planets_tail = self.previous_planets[-1]

        self.previous_planets.appendleft(self.current_planet)
        self.previous_planet = self.current_planet
        self.current_planet = new_planet
        self.current_planet.visited = True
        self.current_planet.clear_samples_today()

    def record_sale(self, item_name, quantity, price):
        self.transaction_log.append((False, self.day, self.current_planet.full_name, item_name, quantity, price))

    def record_purchase(self, item_name, quantity, price):
        self.transaction_log.append((True, self.day, self.current_planet.full_name, item_name, quantity, price))

    def read_transaction_log(self):
        lines = []

        for bought, daynum, planetname, itemname, quantity, price in self.transaction_log:
            if bought:
                line = translate("State", "Day {0}: {1}, bought %Ln {2} for {3} each",
                                 "{1} is a planet name, and {2} is an item name, e.g. tin", quantity)
            else:
                line = translate("State", "Day {0}: {1}, sold %Ln {2} for {3} each",
                                 "{1} is a planet name, and {2} is an item name, e.g. tin", quantity)

            lines.append(line.format(formatNumber(daynum), planetname, itemDisplayName(itemname), formatNumber(price)))

        return '\n'.join(lines)

    def read_travel_log(self):
        return '\n'.join(translate("State", "Day {0}: {1}", "{1} is a planet name").format(formatNumber(daynum), name)
                         for name, daynum in self.travel_log)

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
        self.current_planet.clear_samples_today()
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

        new_planets = Planet.random(num=num_new, used_names=self.used_planet_names)
        low, high = self.discovery_distances()
        for new in new_planets:
            new.discovery_day = self.day

            # Random position between 'low' and 'high' ly from home (which is at 0, 0),
            # spread evenly over that area
            distance = math.sqrt(random.uniform(low ** 2, high ** 2))
            angle = random.uniform(0.0, 2.0 * math.pi)
            new.x = distance * math.cos(angle)
            new.y = distance * math.sin(angle)

            new.items = ItemCollection.random(value_multiplier=self.level * self.remote_price_factor(distance),
                                              quantity_multiplier=self.level)

        self.planets += new_planets
        self.planets_discovered += num_new
