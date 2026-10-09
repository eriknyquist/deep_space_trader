import math
import random

import pytest

from deep_space_trader import constants as const
from deep_space_trader import game_state
from deep_space_trader.game_state import State, health_loss_ranges_by_battle_level

from helpers import give


@pytest.fixture
def state():
    random.seed(10)
    return State(None)


def test_new_game(state):
    assert len(state.planets) == const.INITIAL_PLANET_COUNT
    assert state.current_planet is state.planets[0]
    assert state.current_planet.visited
    assert state.money == const.INITIAL_MONEY
    assert state.day == 1
    assert state.health == 100
    assert state.planets_discovered == const.INITIAL_PLANET_COUNT
    assert state.used_planet_names == {p.full_name for p in state.planets}


def test_change_current_planet_tracks_previous_planets(state):
    a, b, c, d = state.planets[:4]
    state.change_current_planet(b)
    assert state.current_planet is b
    assert state.previous_planet is a
    assert list(state.previous_planets) == [a]
    assert b.visited

    state.change_current_planet(c)
    state.change_current_planet(d)
    assert state.previous_planet is c
    assert list(state.previous_planets) == [c, b]
    # The planet that dropped off the list, so its colour can be cleared
    assert state.previous_planets_tail is a


def test_travel_log(state):
    b, c = state.planets[1:3]
    state.change_current_planet(b)
    state.next_day()
    state.change_current_planet(c)
    assert state.read_travel_log() == "Day 1: %s\nDay 2: %s" % (b.full_name, c.full_name)


def test_transaction_log(state):
    planet = state.current_planet.full_name
    state.record_purchase("tin", 5, 12)
    state.record_sale("jade stone", 1, 2000)
    assert state.read_transaction_log() == (
        "Day 1: %s, bought 5 tin for 12 each\n"
        "Day 1: %s, sold 1 jade stone for 2,000 each" % (planet, planet))


def test_next_day_charges_daily_cost_and_resets_limits(state):
    state.money = 1000
    state.warehouse_trips = 2
    state.store_purchases = 3
    assert state.next_day()
    assert state.day == 2
    assert state.money == 1000 - state.daily_cost
    assert state.warehouse_trips == 0
    assert state.store_purchases == 0


def test_health_recovers_each_day_up_to_100(state):
    state.health = 50
    state.next_day()
    assert state.health == 65

    state.health = 95
    state.next_day()
    assert state.health == 100


def test_no_health_recovery_after_a_pirate_battle(state):
    state.health = 50
    state.disable_health_recovery_today()
    state.next_day()
    assert state.health == 50

    state.next_day()
    assert state.health == 65


def test_starving_costs_health(state):
    state.money = 0
    state.health = 50
    state.next_day()
    assert state.health == 35


def test_last_day(state):
    state.day = state.max_days
    assert not state.next_day()
    assert state.day == state.max_days


@pytest.mark.parametrize("worth, chance", [
    (0, 0.0),
    (1000001, 5.0),
    (10000001, 15.0),
    (50000001, 30.0),
    (500000001, 60.0),
    (1000000001, 80.0),
    (100000000001, 90.0),
])
def test_chance_of_being_robbed_grows_with_net_worth(state, worth, chance):
    state.items.remove_all_items()
    state.money = worth
    assert state.chance_of_being_robbed_in_transit() == chance


def test_net_worth_counts_ship_items_and_optionally_warehouse(state):
    state.money = 100
    give(state.items, "tin", 10)
    give(state.warehouse, "gold", 10)
    assert state.net_worth() == 100 + state.items.total_value
    assert state.net_worth(include_warehouse=True) == 100 + state.items.total_value + state.warehouse.total_value


@pytest.mark.parametrize("level, chance", [(0, 1.0), (3, 30.0), (10, 99.0)])
def test_battle_win_chance_depends_on_battle_level(state, monkeypatch, level, chance):
    asked = []
    monkeypatch.setattr(game_state, "percentChance", lambda p: asked.append(p) or True)
    state.battle_level = level
    assert state.battle_won()
    assert asked == [chance]


@pytest.mark.parametrize("level", range(const.MAX_BATTLE_LEVEL + 1))
def test_health_lost_in_battle_depends_on_battle_level(state, level):
    random.seed(level)
    lower, upper = health_loss_ranges_by_battle_level[level]
    state.battle_level = level
    for _ in range(50):
        state.health = 100
        state.lost_health_from_battle()
        assert lower * 10 <= 100 - state.health <= upper * 10


def test_health_never_goes_below_zero(state):
    state.health = 5
    state.lost_health_from_battle()
    assert state.health == 0


def test_expand_planets(state):
    before = list(state.planets)
    state.day = 7
    state.expand_planets(25)

    new = state.planets[len(before):]
    assert len(new) == 25
    assert state.planets[:len(before)] == before
    assert state.planets_discovered == const.INITIAL_PLANET_COUNT + 25
    assert all(p.discovery_day == 7 for p in new)
    assert all(p.items.count() > 0 for p in new)
    names = [p.full_name for p in state.planets]
    assert len(set(names)) == len(names)


def test_destroyed_planet_names_are_not_reused(state):
    destroyed = state.planets.pop()
    random.seed(11)
    state.expand_planets(3000)
    assert destroyed.full_name not in {p.full_name for p in state.planets}


# ----- Distances and travel -----

def test_home_planet_is_at_the_centre(state):
    assert state.home_planet is state.planets[0]
    assert state.current_planet is state.home_planet
    assert (state.home_planet.x, state.home_planet.y) == (0.0, 0.0)


def test_starting_planets_are_near_home(state):
    for planet in state.planets:
        assert planet.distance_to(state.home_planet) <= const.INITIAL_GALAXY_RADIUS


def test_distance_between_planets(state):
    a, b = state.planets[1:3]
    a.x, a.y = 3.0, 0.0
    b.x, b.y = 0.0, 4.0
    assert a.distance_to(b) == b.distance_to(a) == 5.0


@pytest.mark.parametrize("level", [1, 2, const.MAX_SCOUT_LEVEL])
def test_scouts_find_planets_further_away(state, level):
    state.scout_level = level
    assert state.discovery_distances() == (const.INITIAL_GALAXY_RADIUS, const.INITIAL_GALAXY_RADIUS * (level + 1))

    random.seed(level)
    start = len(state.planets)
    state.expand_planets(400)
    distances = [p.distance_to(state.home_planet) for p in state.planets[start:]]
    low, high = state.discovery_distances()
    assert all(low <= d <= high for d in distances)
    # Spread over the whole range, not bunched at one end
    assert min(distances) < low + (high - low) * 0.2
    assert max(distances) > high - (high - low) * 0.2


def test_travel_cost_grows_with_distance(state):
    target = state.planets[1]
    target.x, target.y = 20.0, 0.0
    assert state.travel_cost_to(target) == round(20 * const.TRAVEL_COST_PER_LY)

    target.x = 200.0
    assert state.travel_cost_to(target) == round(200 * const.TRAVEL_COST_PER_LY)


def test_travel_cost_has_a_minimum(state):
    target = state.planets[1]
    target.x, target.y = 0.1, 0.0
    assert state.travel_cost_to(target) == const.MIN_TRAVEL_COST


def test_engine_upgrades_make_travel_cheaper(state):
    target = state.planets[1]
    target.x, target.y = 100.0, 0.0
    state.engine_level = 2
    expected = round(100 * const.TRAVEL_COST_PER_LY * const.ENGINE_TRAVEL_COST_FACTOR ** 2)
    assert state.travel_cost_to(target) == expected
    assert state.travel_cost_per_ly() == const.TRAVEL_COST_PER_LY * const.ENGINE_TRAVEL_COST_FACTOR ** 2


@pytest.mark.parametrize("distance, factor", [
    (const.PIRATE_REFERENCE_DISTANCE, 1.0),
    (const.PIRATE_REFERENCE_DISTANCE * 2, 2.0),
    (1.0, const.PIRATE_DISTANCE_FACTOR_RANGE[0]),
    (const.PIRATE_REFERENCE_DISTANCE * 100, const.PIRATE_DISTANCE_FACTOR_RANGE[1]),
])
def test_pirate_chance_grows_with_distance(state, monkeypatch, distance, factor):
    monkeypatch.setattr(state, "chance_of_being_robbed_in_transit", lambda: 10.0)
    target = state.planets[1]
    target.x, target.y = distance, 0.0
    assert state.pirate_chance(target) == pytest.approx(10.0 * factor)


def test_pirate_chance_is_capped(state, monkeypatch):
    monkeypatch.setattr(state, "chance_of_being_robbed_in_transit", lambda: 90.0)
    target = state.planets[1]
    target.x, target.y = 1000.0, 0.0
    assert state.pirate_chance(target) == const.MAX_PIRATE_CHANCE_PERCENTAGE


def test_no_pirates_without_net_worth(state):
    state.money = 0
    state.items.remove_all_items()
    target = state.planets[1]
    target.x, target.y = 1000.0, 0.0
    assert state.pirate_chance(target) == 0.0


def test_remote_price_factor():
    outer = const.INITIAL_GALAXY_RADIUS * (const.MAX_SCOUT_LEVEL + 1)
    assert State.remote_price_factor(0) == 1.0
    assert State.remote_price_factor(const.INITIAL_GALAXY_RADIUS) == 1.0
    assert State.remote_price_factor(outer) == pytest.approx(const.REMOTE_PRICE_FACTOR)
    assert State.remote_price_factor(outer * 2) == pytest.approx(const.REMOTE_PRICE_FACTOR)
    middle = (const.INITIAL_GALAXY_RADIUS + outer) / 2
    assert State.remote_price_factor(middle) == pytest.approx((1.0 + const.REMOTE_PRICE_FACTOR) / 2)


def test_remote_planets_have_cheaper_items(state):
    # Compare average prices relative to each item's base price, near and far
    random.seed(12)
    state.scout_level = const.MAX_SCOUT_LEVEL
    state.expand_planets(1500)

    def relative_prices(planets):
        prices = [i.value / i.type.base_value for p in planets for i in p.items.iter_items()]
        return sum(prices) / len(prices)

    inner, outer = state.discovery_distances()
    near = [p for p in state.planets if inner <= p.distance_to(state.home_planet) < inner + 30]
    far = [p for p in state.planets if p.distance_to(state.home_planet) > outer - 30]
    assert near and far
    assert relative_prices(far) < relative_prices(near) * 0.65


# ----- Clusters -----

def nearest_neighbour_ratio(planets, area):
    """
    Average distance to each planet's nearest neighbour, divided by what it would
    be for planets spread evenly at random over 'area' (about 1.0). Clustered
    planets have a smaller ratio
    """
    total = 0.0
    for p in planets:
        total += min(p.distance_to(q) for q in planets if q is not p)

    expected = 0.5 * math.sqrt(area / len(planets))
    return (total / len(planets)) / expected


def test_planets_are_clustered(state):
    random.seed(13)
    state.scout_level = 3
    start = len(state.planets)
    state.expand_planets(300)
    new = state.planets[start:]
    low, high = state.discovery_distances()
    ratio = nearest_neighbour_ratio(new, math.pi * (high ** 2 - low ** 2))
    # Evenly spread planets give about 1.0 (see the next test); these give about 0.72
    assert ratio < 0.8


def test_planets_are_not_all_clustered(state, monkeypatch):
    # With clustering turned off, planets are spread evenly (ratio close to 1)
    monkeypatch.setattr(const, "CLUSTER_FRACTION", 0.0)
    monkeypatch.setattr(const, "STAR_SYSTEM_SPREAD_LY", 1000.0)
    random.seed(13)
    state.scout_level = 3
    start = len(state.planets)
    state.expand_planets(300)
    new = state.planets[start:]
    low, high = state.discovery_distances()
    assert nearest_neighbour_ratio(new, math.pi * (high ** 2 - low ** 2)) > 0.85


def test_star_systems_are_close_together(state):
    random.seed(14)
    state.scout_level = 2
    state.expand_planets(400)
    pairs = [(a, b) for a, b in zip(state.planets, state.planets[1:])
             if b.letter is not None and (a.name, a.number) == (b.name, b.number)]
    assert pairs
    # Almost all within 3 spreads, allowing for planets moved back inside the scout range
    close = [a.distance_to(b) < 3 * 1.5 * const.STAR_SYSTEM_SPREAD_LY for a, b in pairs]
    assert sum(close) >= 0.95 * len(close)


def test_home_star_system_is_around_home(monkeypatch):
    # Start a game whose home planet is in a star system of three planets
    from deep_space_trader.planet import Planet
    system = [Planet("kandar", 12, letter) for letter in "abc"]
    others = [Planet("zorb%d" % i) for i in range(const.INITIAL_PLANET_COUNT - 3)]
    monkeypatch.setattr(Planet, "random", classmethod(lambda cls, num=1, used_names=None: (system + others)[:num]))
    random.seed(15)
    state = State(None)
    assert state.home_planet is system[0]
    for planet in system[1:]:
        assert planet.distance_to(state.home_planet) < 4 * const.STAR_SYSTEM_SPREAD_LY


def test_later_expeditions_can_join_existing_clusters(state):
    random.seed(16)
    state.scout_level = 2
    state.expand_planets(20)
    clusters = list(state.cluster_centres)
    state.expand_planets(200)
    # Some of the new planets are near the earlier clusters
    near_old = [p for p in state.planets[-200:]
                if any(math.hypot(p.x - cx, p.y - cy) < 2 * const.CLUSTER_SPREAD_LY for cx, cy in clusters)]
    assert len(near_old) > 10
