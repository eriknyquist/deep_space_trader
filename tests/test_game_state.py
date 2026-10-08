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
