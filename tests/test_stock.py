"""
Planet stock drifting back towards its starting amount (see Items.restock and
quantity_fluctuations_plan.md)
"""
import random
import statistics
import time

import numpy
import pytest

from deep_space_trader import constants as const
from deep_space_trader import store
from deep_space_trader.items import (
    Items, ItemCollection, common_item_types, contraband_item_types, quantityRange, restockedQuantity
)
from deep_space_trader.location_browser import TradingConsole
from deep_space_trader.location_picker import PlanetDestructionPicker
from deep_space_trader.planet import Planet

from helpers import give, row_of

TIN = common_item_types[0]


def item(quantity, target):
    items = Items(TIN, quantity, 10)
    items.target_quantity = target
    return items


# ----- The rule -----

def test_half_way_back_after_the_half_life():
    # Without the noise (normal=0), exactly half the gap is gone after the half-life
    half_life = const.STOCK_RECOVERY_HALF_LIFE_DAYS
    assert half_life == 5.0
    assert restockedQuantity(0, 10000, half_life, 0.0) == 5000
    assert restockedQuantity(25000, 10000, half_life, 0.0) == 17500
    assert restockedQuantity(0, 10000, half_life * 2, 0.0) == 7500


def test_bigger_gap_bigger_change():
    # The daily change is proportional to the distance from the target
    first = restockedQuantity(0, 10000, 1, 0.0)
    second = restockedQuantity(first, 10000, 1, 0.0) - first
    left = 0.5 ** (1.0 / const.STOCK_RECOVERY_HALF_LIFE_DAYS)
    assert first == pytest.approx(10000 * (1 - left), abs=1)
    assert second == pytest.approx(first * left, abs=2)


def test_no_days_no_change():
    items = item(1234, 10000)
    items.restock(0)
    assert items.quantity == 1234


def test_settled_stock_wobbles_around_the_target():
    random.seed(3)
    quantities = []
    for _ in range(3000):
        items = item(10000, 10000)
        items.restock(30)
        quantities.append(items.quantity)

    assert statistics.mean(quantities) == pytest.approx(10000, rel=0.005)
    assert statistics.pstdev(quantities) == pytest.approx(10000 * const.STOCK_NOISE_FRACTION, rel=0.1)
    # Not stuck on the target
    assert sum(q == 10000 for q in quantities) < 30


def test_catching_up_many_days_is_like_one_day_at_a_time():
    random.seed(4)
    once, daily = [], []
    for _ in range(3000):
        a = item(0, 10000)
        a.restock(5)
        once.append(a.quantity)

        b = item(0, 10000)
        for _ in range(5):
            b.restock(1)
        daily.append(b.quantity)

    assert statistics.mean(once) == pytest.approx(statistics.mean(daily), rel=0.01)
    assert statistics.pstdev(once) == pytest.approx(statistics.pstdev(daily), rel=0.1)


def test_stock_never_goes_negative():
    random.seed(5)
    for _ in range(2000):
        items = item(0, 20)
        items.restock(1)
        assert items.quantity >= 0
    assert restockedQuantity(numpy.zeros(100), numpy.full(100, 5.0), 1, numpy.full(100, -50.0)).min() == 0


def test_restocking_leaves_prices_alone():
    items = item(0, 10000)
    value, slope = items._value, items.value_slope
    items.restock(10)
    assert items.quantity > 0
    assert (items._value, items.value_slope) == (value, slope)


def test_target_is_the_starting_amount():
    assert Items(TIN, 4321, 10).target_quantity == 4321

    # Two lots of the same item on a new market add up
    merged = ItemCollection([Items(TIN, 100, 10), Items(TIN, 50, 10)])
    assert merged.items[TIN.name].target_quantity == 150


# ----- Lazy updates -----

def other_planets(game, count=2):
    state = game.state
    return [p for p in state.planets if p is not state.current_planet and p is not state.home_planet][:count]


def empty_planet_stock(planet):
    for items in planet.items.iter_items():
        items._quantity = 0


def total_stock(planet):
    return sum(items.quantity for items in planet.items.iter_items())


def test_only_planets_being_looked_at_restock(game):
    state = game.state
    planet = other_planets(game, 1)[0]
    empty_planet_stock(planet)
    empty_planet_stock(state.current_planet)

    game.buttonBar.dayButtonClicked()
    # The current planet is updated every day; others only when looked at
    assert total_stock(state.current_planet) > 0
    assert total_stock(planet) == 0


def test_arriving_restocks(game, monkeypatch):
    monkeypatch.setattr(game.state, "pirate_chance", lambda planet: 0)
    planet = other_planets(game, 1)[0]
    empty_planet_stock(planet)
    game.buttonBar.dayButtonClicked()
    game.locationBrowser.travelToPlanet(planet)
    assert game.state.current_planet is planet
    assert total_stock(planet) > 0


def test_trading_console_restocks(game):
    planet = other_planets(game, 1)[0]
    empty_planet_stock(planet)
    game.state.day = 5
    TradingConsole(game, planet)
    assert total_stock(planet) > 0


def test_planets_found_later_restock_from_their_discovery_day():
    planet = Planet("Test")
    planet.discovery_day = 10
    assert planet.stock_days_behind(10) == 0
    assert planet.stock_days_behind(14) == 4
    planet.update_stock(14)
    assert planet.stock_days_behind(14) == 0
    assert planet.stock_days_behind(16) == 2


def test_looking_twice_on_the_same_day_changes_nothing(game):
    planet = other_planets(game, 1)[0]
    empty_planet_stock(planet)
    game.state.day = 5
    planet.update_stock(5)
    stock = [items.quantity for items in planet.items.iter_items()]
    planet.update_stock(5)
    assert [items.quantity for items in planet.items.iter_items()] == stock


def test_bought_out_items_come_back(game):
    from deep_space_trader.transaction_dialogs import Buy

    state = game.state
    planet = state.current_planet
    name = max(planet.items.items, key=lambda n: planet.items.items[n].quantity)
    stock = planet.items.items[name]
    stock._quantity = 50
    stock.target_quantity = 100000
    state.capacity = 10 ** 6

    dialog = Buy(game, name)
    dialog.maxButtonClicked()
    dialog.acceptButtonClicked()
    assert stock.quantity == 0

    # Half way back after the half-life
    for _ in range(int(const.STOCK_RECOVERY_HALF_LIFE_DAYS)):
        game.buttonBar.dayButtonClicked()
    assert stock.quantity == pytest.approx(50000, rel=0.15)


def test_black_markets_restock(game):
    from deep_space_trader.items import Items as ItemsClass
    planet = other_planets(game, 1)[0]
    planet.black_market = True
    planet.items.items[contraband_item_types[0].name] = ItemsClass(contraband_item_types[0], 1000)
    planet.items.items[contraband_item_types[0].name]._quantity = 0
    # About half back after the half-life (from the discovery day, day 1)
    day = 1 + int(const.STOCK_RECOVERY_HALF_LIFE_DAYS)
    game.state.day = day
    planet.update_stock(day)
    assert planet.items.items[contraband_item_types[0].name].quantity == pytest.approx(500, abs=150)


# ----- Free samples -----

def test_accepted_sample_grows_towards_a_normal_amount(game, dialogs, monkeypatch):
    from deep_space_trader.items import rare_item_types

    monkeypatch.setattr(const, "ITEM_SAMPLE_SUCCESS_PERCENT", 100)
    state = game.state
    antimatter = rare_item_types[1]
    state.current_planet.items.items.pop(antimatter.name, None)

    # The player's own antimatter came from somewhere with a huge stock
    give(state.items, antimatter.name, 20)
    state.items.items[antimatter.name].target_quantity = 10 ** 9
    game.playerItemBrowser.update()
    game.playerItemBrowser.table.setCurrentCell(row_of(game.playerItemBrowser.table, antimatter.name), 0)
    game.playerItemBrowser.sellButtonClicked()

    target = state.current_planet.items.items[antimatter.name].target_quantity
    low, high = quantityRange(antimatter)
    assert low * state.level <= target <= high * state.level


# ----- The destruction window: every planet at once -----

def test_catch_up_planets(game):
    state = game.state
    planets = other_planets(game, 2)
    for planet in planets:
        empty_planet_stock(planet)
    histories = {id(i): len(i.value_history) for p in planets for i in p.items.iter_items()}
    state.day = 8

    state.catch_up_planets(planets)
    for planet in planets:
        assert total_stock(planet) > 0
        assert planet.prices_days_behind(8) == 0
        assert planet.stock_days_behind(8) == 0
        for items in planet.items.iter_items():
            # One price per day caught up (prices change from day 1)
            assert len(items.value_history) == histories[id(items)] + 7
            assert items._value > 0.999

    # Already up to date: nothing changes
    before = [(i._value, i.quantity, len(i.value_history)) for p in planets for i in p.items.iter_items()]
    state.catch_up_planets(planets)
    assert [(i._value, i.quantity, len(i.value_history)) for p in planets for i in p.items.iter_items()] == before


def test_catch_up_planets_behaves_like_one_planet_at_a_time(game):
    # Many copies of the same item, caught up 10 days both ways
    state = game.state
    state.day = 11

    def market():
        planet = Planet("Test")
        planet.items = ItemCollection([Items(TIN, 0, 500)])
        planet.items.items[TIN.name].target_quantity = 10000
        planet.items.items[TIN.name]._daily_variance = 1.0
        planet.items.items[TIN.name].value_slope = 0.0
        return planet

    random.seed(6)
    fast = [market() for _ in range(2000)]
    state.catch_up_planets(fast)
    slow = [market() for _ in range(2000)]
    for planet in slow:
        planet.update_prices(11)
        planet.update_stock(11)

    def stats(planets, what):
        values = [what(p.items.items[TIN.name]) for p in planets]
        return statistics.mean(values), statistics.pstdev(values)

    for what in (lambda i: i.quantity, lambda i: i._value):
        (fast_mean, fast_spread), (slow_mean, slow_spread) = stats(fast, what), stats(slow, what)
        assert fast_mean == pytest.approx(slow_mean, rel=0.02, abs=1)
        assert fast_spread == pytest.approx(slow_spread, rel=0.1)


def test_destruction_window_brings_prices_and_stock_up_to_date(game):
    state = game.state
    planet = other_planets(game, 1)[0]
    empty_planet_stock(planet)
    state.day = 6
    PlanetDestructionPicker(game, store.PlanetDestruction(game))
    assert total_stock(planet) > 0
    assert planet.prices_days_behind(6) == 0


def test_destruction_window_is_quick_with_many_planets(big_galaxy):
    # 20,000 planets with 6 items each (about as many as random markets have),
    # none looked at for 30 days
    game = big_galaxy
    state = game.state
    types = common_item_types + list(contraband_item_types[:2])
    for planet in state.planets:
        planet.items = ItemCollection([Items(t, 5000, 50) for t in types])
    state.day = 30

    start = time.time()
    PlanetDestructionPicker(game, store.PlanetDestruction(game))
    assert time.time() - start < 4
    assert all(p.prices_days_behind(30) == 0 for p in state.planets if p is not state.home_planet)


def test_quantity_ranges_work_for_copied_items():
    import copy
    from deep_space_trader.items import rare_item_types, medium_rare_item_types
    assert quantityRange(copy.deepcopy(rare_item_types[0])) == const.RARE_QUANTITY_RANGE
    assert quantityRange(copy.deepcopy(medium_rare_item_types[0])) == const.MEDIUM_RARE_QUANTITY_RANGE
    assert quantityRange(copy.deepcopy(contraband_item_types[0])) == const.BLACK_MARKET_QUANTITY_RANGE
    assert quantityRange(copy.deepcopy(TIN)) == const.COMMON_QUANTITY_RANGE
