import math
import os
import random

import pytest
from PyQt5 import QtCore, QtGui, QtWidgets

from deep_space_trader import constants as const
from deep_space_trader import contraband, store
from deep_space_trader.contraband import BRIBE, FLEE, LET_THEM_SEARCH
from deep_space_trader.item_browsers import CONTRABAND_COLOR, itemNameCell
from deep_space_trader.items import (
    Items, ItemCollection, contraband_item_types, isContraband, rare_item_types
)
from deep_space_trader.location_browser import BLACK_MARKET_COLOR, SURRENDER, TradingConsole
from deep_space_trader.location_picker import PlanetDestructionPicker, VALUE_COLUMN
from deep_space_trader.star_map import StarMap, BLACK_MARKET_COLOR as MAP_BLACK_MARKET_COLOR

from helpers import ALL_ITEM_NAMES, CONTRABAND_NAMES, give, row_of, column

TOBACCO = "untaxed tobacco"
AMMUNITION = "military ammunition"


def contraband_type(name):
    return next(t for t in contraband_item_types if t.name == name)


def make_black_market(planet, prices):
    """
    Make 'planet' a black market trading contraband at 'prices' ({item name: price})
    """
    planet.black_market = True
    for name, price in prices.items():
        items = Items(contraband_type(name), 1000)
        items.value = price
        items.value_history = [price]
        planet.items.items[name] = items


def other_planet(game, n=0):
    """
    A planet that isn't home or the current planet, and isn't a black market
    """
    state = game.state
    planets = [p for p in state.planets if p is not state.home_planet and p is not state.current_planet]
    planet = planets[n]
    planet.black_market = False
    for name in CONTRABAND_NAMES:
        planet.items.items.pop(name, None)

    return planet


def travel(game, planet):
    game.locationBrowser.travelToPlanet(planet)
    assert game.state.current_planet is planet


@pytest.fixture
def no_pirates(game, monkeypatch):
    monkeypatch.setattr(game.state, "pirate_chance", lambda planet: 0)


@pytest.fixture
def lucky(monkeypatch):
    """
    Every chance succeeds (a bribe works, fleeing escapes, a hidden hold hides
    everything), except chances of 0
    """
    monkeypatch.setattr(random, "random", lambda: 0.0)


@pytest.fixture
def unlucky(monkeypatch):
    """
    Every chance fails, except chances of 100
    """
    monkeypatch.setattr(random, "random", lambda: 0.999999)


# ----- Item types and black markets -----

def test_contraband_types():
    assert CONTRABAND_NAMES == ["untaxed tobacco", "bootleg liquor", "combat stimulants",
                                "counterfeit credit chips", "military ammunition"]
    assert not set(CONTRABAND_NAMES) & set(ALL_ITEM_NAMES)
    assert all(isContraband(name) for name in CONTRABAND_NAMES)
    assert not any(isContraband(name) for name in ALL_ITEM_NAMES)

    # Worth more than anything legal
    most_valuable = max(t.base_value for t in rare_item_types)
    assert min(t.base_value for t in contraband_item_types) > most_valuable


def test_ordinary_markets_never_stock_contraband():
    for _ in range(500):
        assert not any(isContraband(name) for name in ItemCollection.random().items)


def test_black_markets_are_spread_evenly(black_markets, big_galaxy):
    state = big_galaxy.state
    planets = state.planets[1:]
    black_markets = [p for p in planets if p.black_market]
    assert len(black_markets) / len(planets) == pytest.approx(const.BLACK_MARKET_CHANCE_PERCENTAGE / 100, abs=0.01)

    # The same share near home and far away
    edge = max(math.hypot(p.x, p.y) for p in planets)
    inner = [p for p in planets if math.hypot(p.x, p.y) < edge / 2]
    outer = [p for p in planets if math.hypot(p.x, p.y) >= edge / 2]
    for group in (inner, outer):
        share = sum(p.black_market for p in group) / len(group)
        assert share == pytest.approx(const.BLACK_MARKET_CHANCE_PERCENTAGE / 100, abs=0.03)

    # No planet starts out found
    assert not any(p.black_market_found for p in planets)


def test_black_market_stock(black_markets, big_galaxy):
    for planet in big_galaxy.state.planets:
        names = [name for name in planet.items.items if isContraband(name)]
        if not planet.black_market:
            assert names == []
            continue

        assert const.BLACK_MARKET_TYPES_RANGE[0] <= len(names) <= const.BLACK_MARKET_TYPES_RANGE[1]
        for name in names:
            item = planet.items.items[name]
            assert const.BLACK_MARKET_QUANTITY_RANGE[0] <= item.quantity <= const.BLACK_MARKET_QUANTITY_RANGE[1]
            low, high = const.BLACK_MARKET_PRICE_FACTOR_RANGE
            assert low * item.type.base_value - 1 <= item.value <= high * item.type.base_value + 1
            assert item.value_history == [item.value]


def test_home_is_never_a_black_market(game, monkeypatch):
    monkeypatch.setattr(const, "BLACK_MARKET_CHANCE_PERCENTAGE", 100.0)
    game.reset()
    state = game.state
    assert not state.home_planet.black_market
    assert not any(isContraband(name) for name in state.home_planet.items.items)
    assert all(p.black_market for p in state.planets[1:])


# ----- Finding black markets -----

def test_first_visit_finds_a_black_market(game, dialogs, no_pirates):
    planet = other_planet(game)
    make_black_market(planet, {TOBACCO: 100})
    travel(game, planet)

    assert planet.black_market_found
    assert dialogs.titles("info") == ["Black market found!"]
    assert dialogs.messages("info") == ["You've found a black market on %s! Contraband can be bought "
                                        "and sold here." % planet.full_name]
    assert "BlackMarketSound" in game.audio.played
    assert "PlanetDiscoverySound" not in game.audio.played

    # Only the first time
    dialogs.clear()
    travel(game, other_planet(game, 1))
    travel(game, planet)
    assert dialogs.titles("info") == []


def test_ordinary_planets_are_not_found(game, dialogs, no_pirates):
    planet = other_planet(game)
    travel(game, planet)
    assert not planet.black_market_found
    assert dialogs.titles("info") == []


def row_colours(game, planet):
    """
    (text colour, background colour) of each cell in a planet's row (None for the default)
    """
    table = game.locationBrowser.table
    row = row_of(table, planet)
    ret = []
    for col in range(table.columnCount()):
        item = table.item(row, col)
        fg, bg = item.foreground(), item.background()
        ret.append((None if fg.style() == QtCore.Qt.NoBrush else fg.color().name(),
                    None if bg.style() == QtCore.Qt.NoBrush else bg.color().name()))
    return ret


def name_tooltip(game, planet):
    table = game.locationBrowser.table
    return table.item(row_of(table, planet), 0).toolTip()


RED = BLACK_MARKET_COLOR.name()
GREEN = "#00aa00"


def test_planets_table_marks_found_black_markets(game, no_pirates):
    planet = other_planet(game)
    make_black_market(planet, {TOBACCO: 100})
    game.locationBrowser.update()
    assert row_colours(game, planet) == [(None, None)] * 4
    assert name_tooltip(game, planet) == ""

    travel(game, planet)

    # Red text in every cell, on the green of the current planet
    assert row_colours(game, planet) == [(RED, GREEN)] * 4
    assert name_tooltip(game, planet) == "Black market"

    # Still marked after leaving: as a previous planet, after it's no longer a
    # previous planet (the distances and reputations are new cells each trip),
    # and when the table is rebuilt
    for n in (1, 2, 3):
        travel(game, other_planet(game, n))
        assert [fg for fg, bg in row_colours(game, planet)] == [RED] * 4

    assert [bg for fg, bg in row_colours(game, planet)] == [None] * 4
    game.locationBrowser.update()
    assert row_colours(game, planet) == [(RED, None)] * 4
    assert name_tooltip(game, planet) == "Black market"

    # Other planets' text is left alone
    assert row_colours(game, other_planet(game, 4)) == [(None, None)] * 4


def test_trading_console_hides_black_markets_not_found(game):
    state = game.state
    planet = other_planet(game)
    make_black_market(planet, {TOBACCO: 100})
    legal = [name for name in planet.items.items if not isContraband(name)]

    shown = column(TradingConsole(game, planet).findChild(QtWidgets.QTableWidget), 0)
    assert sorted(shown) == sorted(legal)
    assert state.shown_item_names(planet) == legal

    planet.black_market_found = True
    shown = column(TradingConsole(game, planet).findChild(QtWidgets.QTableWidget), 0)
    assert sorted(shown) == sorted(legal + [TOBACCO])


def test_rumours_dont_give_black_markets_away(game, dialogs, monkeypatch):
    planet = other_planet(game)
    planet.items = ItemCollection()
    make_black_market(planet, {TOBACCO: 100})
    monkeypatch.setattr(game.state, "planets", [planet])
    monkeypatch.setattr(const, "CHANCE_TRADING_TIP_PERCENTAGE", 100.0)

    game.runRandomNotifications()
    assert dialogs.titles("info") == []

    planet.black_market_found = True
    game.runRandomNotifications()
    assert dialogs.titles("info") == ["Rumour overheard!"]
    assert TOBACCO in dialogs.messages("info")[0]


def test_destruction_picker_hides_black_markets_not_found(game):
    planet = other_planet(game)
    legal_value = planet.items.total_value
    make_black_market(planet, {TOBACCO: 100})

    def shown_value():
        table = PlanetDestructionPicker(game, store.PlanetDestruction(game)).table
        return table.item(row_of(table, planet), VALUE_COLUMN).text()

    assert shown_value() == "{:,}".format(int(legal_value))
    planet.black_market_found = True
    assert shown_value() == "{:,}".format(int(legal_value + 100 * 1000))


# ----- Selling -----

def select(browser, itemname):
    browser.update()
    browser.table.setCurrentCell(row_of(browser.table, itemname), 0)


def test_contraband_cant_be_sold_off_black_markets(game, dialogs):
    planet = game.state.current_planet
    give(game.state.items, TOBACCO, 10)
    select(game.playerItemBrowser, TOBACCO)
    game.playerItemBrowser.sellButtonClicked()

    assert dialogs.titles("error") == ["Contraband"]
    assert dialogs.messages("error") == ["Nobody on %s will touch untaxed tobacco." % planet.full_name]
    assert dialogs.titles("question") == []     # no free sample offered
    assert game.state.items.items[TOBACCO].quantity == 10
    assert TOBACCO not in planet.items.items


def test_sell_all_leaves_contraband_off_black_markets(game, dialogs):
    state = game.state
    planet = state.current_planet
    legal = next(iter(planet.items.items))
    give(state.items, legal, 10)
    give(state.items, TOBACCO, 10)

    game.playerItemBrowser.sellAllButtonClicked()
    assert list(state.items.items) == [TOBACCO]
    assert state.items.items[TOBACCO].quantity == 10


def test_selling_contraband_on_a_black_market(game, dialogs):
    from deep_space_trader.transaction_dialogs import Sell

    state = game.state
    planet = state.current_planet
    make_black_market(planet, {TOBACCO: 700})
    planet.black_market_found = True
    give(state.items, TOBACCO, 10)
    money = state.money
    reputation = state.reputation_of(planet)

    dialog = Sell(game, TOBACCO)
    dialog.spinbox.setValue(10)
    dialog.acceptButtonClicked()

    assert state.money == money + 10 * 700
    assert TOBACCO not in state.items.items

    # Selling contraband doesn't make anyone like you more
    assert state.reputation_of(planet) == reputation

    # ...but selling legal goods still does
    legal = next(name for name in planet.items.items if not isContraband(name))
    give(state.items, legal, 10)
    dialog = Sell(game, legal)
    dialog.spinbox.setValue(10)
    dialog.acceptButtonClicked()
    assert state.reputation_of(planet) > reputation


def test_sell_all_contraband_on_a_black_market(game, dialogs):
    state = game.state
    planet = state.current_planet
    make_black_market(planet, {TOBACCO: 700})
    give(state.items, TOBACCO, 10)
    money = state.money
    reputation = state.reputation_of(planet)

    game.playerItemBrowser.sellAllButtonClicked()
    assert state.money == money + 7000
    assert state.reputation_of(planet) == reputation


def test_black_markets_can_be_offered_new_contraband_types(game, dialogs):
    planet = game.state.current_planet
    make_black_market(planet, {TOBACCO: 700})
    give(game.state.items, AMMUNITION, 20)
    select(game.playerItemBrowser, AMMUNITION)
    game.playerItemBrowser.sellButtonClicked()
    assert dialogs.titles("question") == ["Provide sample?"]


# ----- Chances -----

def test_inspection_chance_grows_with_the_load(game):
    state = game.state
    planet = other_planet(game)
    assert state.inspection_chance(planet) == 0

    give(state.items, TOBACCO, 100)
    assert state.inspection_chance(planet) == pytest.approx(12.0)
    give(state.items, AMMUNITION, 900)
    assert state.inspection_chance(planet) == pytest.approx(30.0)

    # Legal goods and the warehouse don't count
    give(state.items, "tin", 5000)
    give(state.warehouse, TOBACCO, 5000)
    assert state.inspection_chance(planet) == pytest.approx(30.0)

    give(state.items, TOBACCO, 10000)
    assert state.inspection_chance(planet) == const.MAX_INSPECTION_CHANCE_PERCENTAGE


def test_inspection_chance_grows_with_bad_reputation(game):
    state = game.state
    planet = other_planet(game)
    give(state.items, TOBACCO, 500)
    assert state.inspection_chance(planet) == pytest.approx(20.0)

    state.customs_event(planet, -35)
    reputation = state.reputation_of(planet)
    assert reputation < const.FRIENDLY_REPUTATION
    factor = 1 + (const.FRIENDLY_REPUTATION - reputation) / const.FRIENDLY_REPUTATION
    assert state.inspection_chance(planet) == pytest.approx(20.0 * factor)


def test_bribe_and_flee_chances(game):
    state = game.state
    planet = other_planet(game)
    assert state.bribe_success_chance(planet) == const.BRIBE_SUCCESS_PERCENTAGE

    state.customs_event(planet, -100)
    assert state.reputation_of(planet) == 0
    assert state.bribe_success_chance(planet) == 35.0

    assert state.flee_escape_chance() == 30.0
    state.engine_level = 5
    assert state.flee_escape_chance() == 60.0
    state.engine_level = 10
    assert state.flee_escape_chance() == const.MAX_FLEE_ESCAPE_PERCENTAGE


def test_contraband_value(game):
    state = game.state
    planet = other_planet(game)
    give(state.items, TOBACCO, 10)
    give(state.items, AMMUNITION, 2)
    give(state.items, "tin", 1000)

    # Base prices, unless the planet trades it
    assert state.contraband_value(planet) == 10 * const.PRICE_TOBACCO + 2 * const.PRICE_AMMUNITION
    make_black_market(planet, {TOBACCO: 1000})
    assert state.contraband_value(planet) == 10 * 1000 + 2 * const.PRICE_AMMUNITION


# ----- Inspection outcomes -----

@pytest.fixture
def cargo(game):
    """
    The game, with 10 untaxed tobacco (worth 2,500) and 50 tin on the ship, and
    100,000 money. Returns the destination of the trip
    """
    state = game.state
    give(state.items, TOBACCO, 10)
    give(state.items, "tin", 50)
    state.money = 100000
    return other_planet(game)


@pytest.fixture
def events(game, monkeypatch):
    """
    Reputation changes, as (x, y, change, spread)
    """
    ret = []
    monkeypatch.setattr(game.state.reputation, "addEvent", lambda *event: ret.append(event))
    return ret


def customs_events(cargo, *changes):
    """
    The reputation events expected at the trip's destination, for 'changes'
    ((change, spread) pairs)
    """
    return [(cargo.x, cargo.y, change, spread) for change, spread in changes]


def test_let_them_search(game, cargo, unlucky, events):
    state = game.state
    outcome = contraband.let_them_search(state, cargo)

    assert outcome.searched and outcome.found
    assert outcome.seized_value == 2500
    assert outcome.fine == 2500
    assert state.money == 100000 - 2500
    assert list(state.items.items) == ["tin"]
    assert events == customs_events(cargo, (const.CONTRABAND_FOUND_REPUTATION, const.TRADE_SPREAD_LY))


def test_fine_is_limited_to_your_money(game, cargo, unlucky):
    game.state.money = 1000
    outcome = contraband.let_them_search(game.state, cargo)
    assert outcome.fine == 1000
    assert game.state.money == 0


def test_hidden_hold_can_hide_everything(game, cargo, lucky, events):
    state = game.state

    # Without a hidden hold, even the luckiest search finds everything
    outcome = contraband.let_them_search(state, cargo)
    assert outcome.found

    give(state.items, TOBACCO, 10)
    state.money = 100000
    state.hidden_hold_level = 1
    events.clear()
    outcome = contraband.let_them_search(state, cargo)
    assert outcome.searched and not outcome.found
    assert outcome.fine == 0
    assert state.money == 100000
    assert state.items.items[TOBACCO].quantity == 10
    assert events == []


@pytest.mark.parametrize("level", [1, 2, 3])
def test_hidden_hold_chance(game, level):
    state = game.state
    state.hidden_hold_level = level
    planet = other_planet(game)
    hidden = 0
    for _ in range(3000):
        give(state.items, TOBACCO, 1)
        hidden += not contraband.search(state, planet, contraband.Outcome()).found
        state.items.remove_all_items()

    expected = const.HIDDEN_HOLD_NOTHING_FOUND_PERCENTAGES[level - 1] / 100
    assert hidden / 3000 == pytest.approx(expected, abs=0.04)


def test_bribe_works(game, cargo, lucky, events):
    state = game.state
    outcome = contraband.bribe(state, cargo)

    assert outcome.bribed and not outcome.searched
    assert outcome.bribe_paid == 750
    assert state.money == 100000 - 750
    assert state.items.items[TOBACCO].quantity == 10
    assert events == []


def test_bribe_fails(game, cargo, unlucky, events):
    state = game.state
    outcome = contraband.bribe(state, cargo)

    assert outcome.bribe_failed and outcome.searched and outcome.found
    assert state.money == 100000 - 750 - 2500
    assert TOBACCO not in state.items.items
    assert events == customs_events(cargo, (const.FAILED_BRIBE_REPUTATION, const.TRADE_SPREAD_LY))


def test_flee_and_escape(game, cargo, lucky, events):
    state = game.state
    outcome = contraband.flee(state, cargo)

    assert outcome.escaped and not outcome.searched
    assert state.money == 100000
    assert state.health == 100
    assert state.items.items[TOBACCO].quantity == 10
    assert events == customs_events(cargo, (const.ESCAPED_PATROL_REPUTATION, const.TRADE_SPREAD_LY))


def test_flee_and_get_caught(game, cargo, unlucky, events):
    state = game.state
    outcome = contraband.flee(state, cargo)

    # Damaged as in a lost battle (with no battle fleet, 70 to 90 health)
    assert outcome.caught and outcome.found
    assert 10 <= state.health <= 30
    assert state.no_health_recovery
    assert state.money == 100000 - 2500

    # The news spreads further than other customs news
    assert events == customs_events(cargo, (const.CAUGHT_FLEEING_REPUTATION, const.DESTRUCTION_SPREAD_LY))


# ----- Inspections while travelling -----

@pytest.fixture
def inspected(game, monkeypatch, no_pirates):
    """
    Every trip with contraband on the ship gets inspected
    """
    monkeypatch.setattr(const, "INSPECTION_CHANCE_PERCENTAGE", 100.0)
    monkeypatch.setattr(const, "MAX_INSPECTION_CHANCE_PERCENTAGE", 100.0)


def test_travel_prompt_warns_about_contraband(game, dialogs, cargo, no_pirates):
    game.state.items.remove_items(TOBACCO, 10)
    travel(game, other_planet(game, 1))
    assert "contraband" not in dialogs.messages("question")[0]

    give(game.state.items, TOBACCO, 10)
    chance = game.state.inspection_chance(cargo)
    dialogs.clear()
    travel(game, cargo)
    assert ("You're carrying contraband worth 2,500. Chance of a customs inspection: %d%%." % round(chance)) \
        in dialogs.messages("question")[0]


def test_inspection_during_travel(game, dialogs, cargo, inspected, unlucky):
    state = game.state
    day = state.day
    dialogs.choices["Customs"] = LET_THEM_SEARCH
    travel(game, cargo)

    assert dialogs.titles("choice") == ["Customs inspection!"]
    assert dialogs.choices_offered == ["Bribe", "Flee", "Let them search"]
    message = dialogs.messages("choice")[0]
    assert "You're carrying contraband worth 2,500." in message
    assert "pay the officers 750 to look the other way. This works 70% of the time." in message
    assert "Your chance of escaping is 30%." in message
    assert "your contraband is seized, and you're fined 2,500." in message

    # You still arrive, and the day passes
    assert state.day == day + 1
    assert dialogs.titles("info") == ["Searched"]
    assert dialogs.messages("info") == ["The officers search your ship, seize your contraband "
                                        "(worth 2,500), and fine you 2,500."]
    assert TOBACCO not in column(game.playerItemBrowser.table, 0)

    # A siren when the patrol stops the ship, then the outcome's sound
    sounds = game.audio.played
    assert sounds.index("SirenSound") < sounds.index("FailureSound")
    assert "BattleSound" not in sounds


@pytest.mark.parametrize("choice, luck, title", [
    (BRIBE, "lucky", "Bribe accepted"),
    (BRIBE, "unlucky", "Bribe refused"),
    (FLEE, "lucky", "Escaped!"),
    (FLEE, "unlucky", "Caught!"),
])
def test_inspection_outcome_messages(game, dialogs, cargo, inspected, request, choice, luck, title):
    request.getfixturevalue(luck)
    game.state.battle_level = 10
    dialogs.choices["Customs"] = choice
    travel(game, cargo)
    assert dialogs.titles("info") == [title]


def test_inspection_with_hidden_hold(game, dialogs, cargo, inspected, lucky):
    game.state.hidden_hold_level = 2
    dialogs.choices["Customs"] = LET_THEM_SEARCH
    travel(game, cargo)
    assert "there's a 45% chance they won't find your hidden cargo hold" in dialogs.messages("choice")[0]
    assert dialogs.messages("info") == ["The officers search your ship, but don't find your hidden "
                                        "cargo hold. Your contraband is safe."]
    assert game.state.items.items[TOBACCO].quantity == 10


def test_bribe_disabled_when_you_cant_afford_it(game, dialogs, cargo, inspected, unlucky):
    game.state.money = game.state.travel_cost_to(cargo) + 500

    # (The fine takes all your money, so you lose health at the end of the day.
    # Don't die of that too)
    game.state.battle_level = 10
    travel(game, cargo)
    assert dialogs.choices_enabled == [False, True, True]
    assert "the officers want 750, which is more than you have." in dialogs.messages("choice")[0]

    # The first choice that can be made: flee
    assert dialogs.titles("info") == ["Caught!"]


def test_death_when_caught_fleeing(game, dialogs, cargo, inspected, unlucky):
    game.state.health = 10
    dialogs.choices["Customs"] = FLEE
    game.locationBrowser.travelToPlanet(cargo)

    assert dialogs.titles("info") == ["Caught!"]
    assert "You are dead." in dialogs.messages("info")[0]
    assert game.state.day == 1
    assert game.state.current_planet is game.state.home_planet
    assert game.state.health == 100


def test_no_inspection_without_contraband(game, dialogs, inspected):
    give(game.state.items, "tin", 50)
    give(game.state.warehouse, TOBACCO, 50)
    for n in range(5):
        travel(game, other_planet(game, n))

    assert dialogs.titles("choice") == []


def test_no_inspection_after_pirates(game, dialogs, cargo, inspected, monkeypatch):
    monkeypatch.setattr(game.state, "pirate_chance", lambda planet: 100)
    dialogs.choices["pirate"] = SURRENDER
    travel(game, cargo)
    assert dialogs.titles("choice") == ["Attacked by pirates!"]


# ----- Hidden cargo hold -----

def test_hidden_cargo_hold_store_item(game, dialogs):
    game.state.max_store_purchases_per_day = 1000
    shop = store.Store(game)
    item = next(i for i in store.store_items if isinstance(i, store.HiddenCargoHold))
    row = store.store_items.index(item)

    assert shop.table.item(row, 0).text() == "Hidden cargo hold"
    assert "there's a 25% chance they don't find your contraband" in item.description

    money = game.state.money
    for level, cost in enumerate(const.HIDDEN_HOLD_COSTS, 1):
        assert item.price == cost
        shop.buyItem(item)
        assert game.state.hidden_hold_level == level

    assert game.state.money == money - sum(const.HIDDEN_HOLD_COSTS)
    assert item.price is None
    assert shop.table.item(row, 2).text() == "\u2013"
    assert item.name == "Improve hidden cargo hold"

    # A new game starts without one
    game.reset()
    item = next(i for i in store.store_items if isinstance(i, store.HiddenCargoHold))
    assert game.state.hidden_hold_level == 0
    assert item.price == const.HIDDEN_HOLD_COSTS[0]
    assert item.name == "Hidden cargo hold"


def test_hidden_cargo_hold_upgrade_description(game, dialogs):
    item = store.HiddenCargoHold(game)
    item.use()
    item.after_use()
    assert item.description == ("Hide your secret compartment better. The chance that a customs search "
                                "doesn't find your contraband goes from 25% to 45%.")


# ----- Display -----

def test_contraband_names_are_red():
    cell = itemNameCell(TOBACCO)
    assert cell.foreground().color() == CONTRABAND_COLOR
    assert cell.toolTip().startswith("Contraband:")

    cell = itemNameCell("tin")
    assert cell.foreground().style() == QtCore.Qt.NoBrush
    assert cell.toolTip() == ""


def test_ship_table_shows_contraband_in_red(game):
    give(game.state.items, TOBACCO, 5)
    game.playerItemBrowser.update()
    table = game.playerItemBrowser.table
    assert table.item(row_of(table, TOBACCO), 0).foreground().color() == CONTRABAND_COLOR


def test_prices_window_lists_contraband(game):
    from deep_space_trader.item_prices import PricesTable

    table = PricesTable(game).table
    texts = column(table, 0)
    heading = texts.index("Contraband (only traded on black markets)")
    assert texts[heading + 1:] == CONTRABAND_NAMES
    assert table.columnSpan(heading, 0) == 2
    assert [table.item(row, 1).text() for row in range(heading + 1, table.rowCount())] == \
        ["250", "300", "400", "600", "800"]


def test_star_map_marks_found_black_markets(game):
    planet = other_planet(game)
    make_black_market(planet, {TOBACCO: 100})
    starmap = StarMap(game)
    assert "Black market" not in starmap.tooltipText(planet)
    assert not any(key[0] for key in starmap.layer.groups)

    planet.visited = planet.black_market_found = True
    starmap = StarMap(game)
    assert "Black market" in starmap.tooltipText(planet)
    assert starmap.planetStyle(planet).ring == MAP_BLACK_MARKET_COLOR
    found = [key for key in starmap.layer.groups if key[0]]
    assert len(found) == 1
    assert len(starmap.layer.groups[found[0]][-1]) == 1


def test_encounter_icons(game, dialogs, cargo, inspected, unlucky):
    make_black_market(cargo, {TOBACCO: 100})
    travel(game, cargo)
    # The inspection, its outcome, and finding the black market
    assert dialogs.titles() == ["Travel", "Customs inspection!", "Bribe refused", "Black market found!"]
    assert dialogs.icons == ["customs", "customs", "black_market"]


@pytest.mark.parametrize("dpr", [1.0, 2.0])
@pytest.mark.parametrize("name", ["pirates", "customs", "black_market"])
def test_icons(qapp, name, dpr):
    from deep_space_trader import icons
    pixmap = icons.iconPixmap(name, 64, dpr)
    assert pixmap.devicePixelRatio() == dpr
    image = pixmap.toImage()
    assert (image.width(), image.height()) == (64 * dpr, 64 * dpr)

    # Something is drawn, and the corners are see-through
    colours = {image.pixel(x, y) for x in range(0, image.width(), 2) for y in range(0, image.height(), 2)}
    assert len(colours) > 5
    assert QtGui.qAlpha(image.pixel(0, image.height() - 1)) == 0


def test_icon_files_are_large_enough(qapp):
    from deep_space_trader import icons
    from deep_space_trader.utils import IMAGE_DIR
    for filename in icons.FILENAMES.values():
        image = QtGui.QImage(os.path.join(IMAGE_DIR, filename))
        assert (image.width(), image.height()) == (icons.FILE_SIZE, icons.FILE_SIZE)
        assert image.hasAlphaChannel()


def test_icon_script(qapp, tmp_path):
    # The script that makes the icon files still works
    import importlib.util
    path = os.path.join(os.path.dirname(__file__), os.pardir, "scripts", "make_icons.py")
    spec = importlib.util.spec_from_file_location("make_icons", path)
    make_icons = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(make_icons)

    make_icons.main(["--output", str(tmp_path)])
    from deep_space_trader import icons
    assert sorted(os.listdir(tmp_path)) == sorted(icons.FILENAMES.values())
    assert QtGui.QImage(str(tmp_path / icons.FILENAMES[icons.PIRATES])).width() == icons.FILE_SIZE