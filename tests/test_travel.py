import pytest
from PyQt5 import QtCore, QtTest

from deep_space_trader import location_browser
from deep_space_trader.location_browser import TradingConsole

from helpers import give, row_of, column


CURRENT = "#00aa00/255"
PREVIOUS = "#00aa00/125"
BEFORE_PREVIOUS = "#00aa00/50"


def colour(table, row):
    brush = table.item(row, 0).background()
    if brush.style() == QtCore.Qt.NoBrush:
        return None

    return "%s/%d" % (brush.color().name(), brush.color().alpha())


def expected_colours(game):
    """
    {planet name: (visited, colour)} that the planets table should show
    """
    state = game.state
    previous = [p for p in state.previous_planets if p in state.planets]
    shades = [PREVIOUS, BEFORE_PREVIOUS]
    table = game.locationBrowser.table
    ret = {}
    for row in range(table.rowCount()):
        planet = table.item(row, 0).data(QtCore.Qt.UserRole)
        if planet is state.current_planet:
            c = CURRENT
        elif planet in previous:
            c = shades[previous.index(planet)]
        else:
            c = None
        ret[planet.full_name] = ("yes" if planet.visited else "no", c)
    return ret


def shown_colours(game):
    table = game.locationBrowser.table
    return {table.item(row, 0).text(): (table.item(row, 1).text(), colour(table, row))
            for row in range(table.rowCount())}


def select(game, planet):
    table = game.locationBrowser.table
    table.setCurrentCell(row_of(table, planet), 0)


def search(game, text):
    game.locationBrowser.planetSearchText.clear()
    QtTest.QTest.keyClicks(game.locationBrowser.planetSearchText, text)


@pytest.fixture
def no_pirates(game, monkeypatch):
    monkeypatch.setattr(game.state, "pirate_chance", lambda planet: 0)


@pytest.fixture
def pirates(game, monkeypatch):
    monkeypatch.setattr(game.state, "pirate_chance", lambda planet: 100)


def test_travel(game, dialogs, no_pirates):
    state = game.state
    target = state.planets[3]
    money = state.money
    cost = state.travel_cost_to(target)

    select(game, target)
    game.locationBrowser.travelButtonClicked()

    assert state.current_planet is target
    assert target.visited
    assert state.day == 2
    assert state.money == money - cost - state.daily_cost
    assert dialogs.titles("question") == ["Travel"]
    assert game.audio.played == ["TravelSound"]
    assert game.infoBar.planetLabel.text() == target.full_name


def test_travel_by_double_click(game, no_pirates):
    target = game.state.planets[2]
    select(game, target)
    game.locationBrowser.onDoubleClick(None)
    assert game.state.current_planet is target


def test_travel_declined(game, dialogs, no_pirates):
    start = game.state.current_planet
    dialogs.answers["Travel"] = False
    select(game, game.state.planets[3])
    game.locationBrowser.travelButtonClicked()
    assert game.state.current_planet is start
    assert game.state.day == 1


def test_travel_needs_a_selection(game, dialogs):
    game.locationBrowser.table.setCurrentCell(-1, -1)
    game.locationBrowser.travelButtonClicked()
    assert dialogs.messages("error") == ["Please select a planet to travel to first!"]


def test_travel_without_enough_money(game, dialogs, no_pirates):
    target = game.state.planets[3]
    target.x, target.y = 100.0, 0.0      # cost 500, so the number has no thousands separator
    cost = game.state.travel_cost_to(target)
    game.state.money = cost - 1
    select(game, target)
    game.locationBrowser.travelButtonClicked()
    assert dialogs.messages("error") == ["You don't have enough money! (%d required)" % cost]
    assert game.state.day == 1


def test_travel_to_current_planet(game, dialogs, no_pirates):
    current = game.state.current_planet
    select(game, current)
    game.locationBrowser.travelButtonClicked()
    assert dialogs.messages("error") == ["You are already on %s!" % current.full_name]


def test_travel_to_previous(game, dialogs, no_pirates):
    start = game.state.current_planet
    select(game, game.state.planets[3])
    game.locationBrowser.travelButtonClicked()

    game.locationBrowser.previousButtonClicked()
    assert game.state.current_planet is start
    assert game.state.day == 3


def test_no_previous_planet(game, dialogs):
    game.locationBrowser.previousButtonClicked()
    assert dialogs.messages("error") == ["No previous planet to travel to!"]


def test_previous_planet_destroyed(game, dialogs, no_pirates):
    # Bug 2: travelling back to a destroyed planet used to crash
    start = game.state.current_planet
    select(game, game.state.planets[3])
    game.locationBrowser.travelButtonClicked()
    game.state.planets.remove(start)
    money = game.state.money

    game.locationBrowser.previousButtonClicked()
    assert dialogs.messages("error") == ["%s no longer exists!" % start.full_name]
    assert game.state.money == money


def test_planets_with_the_same_name(game, no_pirates):
    # Bug 15: the game used to find planets by name, so it picked the wrong one
    state = game.state
    first, second = state.planets[2], state.planets[5]
    second._name, second._number, second._letter = first.name, first.number, first.letter
    game.locationBrowser.update()

    select(game, second)
    game.locationBrowser.travelButtonClicked()
    assert state.current_planet is second


def test_planet_colours_after_travelling(game, no_pirates):
    state = game.state
    for planet in state.planets[1:5]:
        select(game, planet)
        game.locationBrowser.travelButtonClicked()
        assert shown_colours(game) == expected_colours(game)

    assert list(shown_colours(game).values()).count(("yes", CURRENT)) == 1
    assert [c for _, c in shown_colours(game).values() if c] == [BEFORE_PREVIOUS, PREVIOUS, CURRENT]


def test_search_filters_planets(game):
    state = game.state
    target = state.planets[-1]
    search(game, target.full_name.upper())
    assert column(game.locationBrowser.table, 0) == [target.full_name]
    assert game.locationBrowserGroup.title() == "Planets (1)"

    game.locationBrowser.planetSearchText.clear()
    assert len(column(game.locationBrowser.table, 0)) == len(state.planets)


def test_travel_while_searching(game, no_pirates):
    # Bug 5: travelling to a planet further down the list than the search
    # results reach used to raise an error and colour the wrong rows
    target = game.state.planets[-1]
    search(game, target.full_name)
    select(game, target)
    game.locationBrowser.travelButtonClicked()

    assert game.state.current_planet is target
    assert shown_colours(game) == {target.full_name: ("yes", CURRENT)}

    game.locationBrowser.planetSearchText.clear()
    assert shown_colours(game) == expected_colours(game)


def test_search_survives_table_refresh(game):
    target = game.state.planets[-1]
    search(game, target.full_name)
    game.state.expand_planets(5)
    game.locationBrowser.update()
    assert column(game.locationBrowser.table, 0) == [target.full_name]


def test_enter_opens_trading_console_for_selected_planet(game, dialogs):
    game.state.enable_trading_console()
    target = game.state.planets[4]
    select(game, target)
    QtTest.QTest.keyClick(game.locationBrowser, QtCore.Qt.Key_Return)
    assert [type(d) for d in dialogs.executed] == [TradingConsole]
    assert dialogs.executed[0].windowTitle() == "Item prices on %s" % target.full_name


def test_enter_without_trading_console(game, dialogs):
    select(game, game.state.planets[4])
    QtTest.QTest.keyClick(game.locationBrowser, QtCore.Qt.Key_Return)
    assert dialogs.executed == []
    assert len(dialogs.messages("error")) == 1


def test_enter_with_no_selection_does_nothing(game, dialogs):
    # Bug 4
    game.state.enable_trading_console()
    game.locationBrowser.table.setCurrentCell(-1, -1)
    QtTest.QTest.keyClick(game.locationBrowser, QtCore.Qt.Key_Enter)
    assert dialogs.executed == []


def test_trading_console_button(game, dialogs):
    game.state.enable_trading_console()
    game.locationBrowser.table.setCurrentCell(-1, -1)
    game.locationBrowser.pricesButtonClicked()
    assert dialogs.messages("error") == ["Please select a planet first!"]

    select(game, game.state.planets[1])
    game.locationBrowser.pricesButtonClicked()
    assert [type(d) for d in dialogs.executed] == [TradingConsole]


def test_win_against_pirates(game, dialogs, pirates, monkeypatch):
    state = game.state
    monkeypatch.setattr(state, "battle_won", lambda: True)
    state.battle_level = 0       # every battle costs 70-90 health at level 0
    give(state.items, "tin", 10)
    money = state.money
    target = state.planets[3]
    cost = state.travel_cost_to(target)

    select(game, target)
    game.locationBrowser.travelButtonClicked()
    assert state.current_planet is target
    assert state.health < 100
    assert state.items.count() == 10
    assert state.money == money - cost - state.daily_cost
    assert dialogs.titles("info") == ["Battle won!"]


def test_no_health_recovery_after_pirate_battle(game, pirates, monkeypatch):
    state = game.state
    monkeypatch.setattr(state, "battle_won", lambda: True)
    monkeypatch.setattr(state, "lost_health_from_battle", lambda: setattr(state, "health", 50))
    select(game, state.planets[3])
    game.locationBrowser.travelButtonClicked()
    assert state.health == 50


def test_dying_from_a_won_pirate_battle(game, dialogs, pirates, monkeypatch):
    # Intended behaviour (problems.md bug 18): a win that uses up all your
    # health still kills you, and is reported as a lost battle
    state = game.state
    monkeypatch.setattr(state, "battle_won", lambda: True)
    state.health = 10
    select(game, state.planets[3])
    game.locationBrowser.travelButtonClicked()
    assert "Battle lost!" in dialogs.titles("info")
    assert state.day == 1
    assert state.health == 100


def test_lose_against_pirates(game, dialogs, pirates, monkeypatch):
    state = game.state
    monkeypatch.setattr(state, "battle_won", lambda: False)
    old_planets = list(state.planets)
    select(game, state.planets[3])
    game.locationBrowser.travelButtonClicked()

    assert dialogs.titles("info")[-1] == "Battle lost!"
    assert game.audio.played[-1] == "DeathSound"
    # A new game has started
    assert state.day == 1
    assert not set(map(id, state.planets)) & set(map(id, old_planets))


def test_surrender_with_items_on_board(game, dialogs, pirates, monkeypatch):
    state = game.state
    dialogs.answers["pirates"] = False
    monkeypatch.setattr(location_browser, "percentChance", lambda p: p == 100)
    give(state.items, "tin", 40)
    game.updatePlayerItemsLabel()
    assert game.playerItemBrowserGroup.title() == "Items on your ship (40/%d)" % state.capacity
    money = state.money
    cost = state.travel_cost_to(state.planets[3])

    select(game, state.planets[3])
    game.locationBrowser.travelButtonClicked()
    assert state.items.count() == 0
    assert state.money == money - cost - state.daily_cost
    # Bug 16: the ship label wasn't updated after the robbery
    assert game.playerItemBrowserGroup.title() == "Items on your ship (0/%d)" % state.capacity
    assert dialogs.titles("info") == ["Surrender"]


def test_surrender_with_empty_ship_loses_money(game, dialogs, pirates):
    state = game.state
    dialogs.answers["pirates"] = False
    state.money = 1000000
    cost = state.travel_cost_to(state.planets[3])
    select(game, state.planets[3])
    game.locationBrowser.travelButtonClicked()
    left = 1000000 - cost
    assert left * 0.01 - state.daily_cost - 1 <= state.money <= left * 0.05


def test_tooltips_can_be_turned_off(game):
    game.enableTooltips(False)
    assert game.locationBrowser.travelButton.toolTip() == ""
    game.enableTooltips(True)
    assert game.locationBrowser.travelButton.toolTip() == "travel to the selected planet"


# ----- Distances -----

def test_travel_prompt_shows_distance_and_cost(game, dialogs, no_pirates):
    state = game.state
    target = state.planets[3]
    target.x, target.y = 30.0, 40.0
    state.money = 5000
    select(game, target)
    game.locationBrowser.travelButtonClicked()
    assert dialogs.messages("question") == [
        "Travel to %s?<br><br>(distance 50.0 ly, cost 250, you have 5,000)" % target.full_name]


def test_travel_home(game, dialogs, no_pirates):
    state = game.state
    home = state.home_planet
    select(game, state.planets[3])
    game.locationBrowser.travelButtonClicked()
    assert state.current_planet is not home

    game.locationBrowser.homeButtonClicked()
    assert state.current_planet is home

    game.locationBrowser.homeButtonClicked()
    assert dialogs.messages("error") == ["You are already on %s!" % home.full_name]


def distance(table, row):
    """
    Distance stored in a row's distance cell (a number, so the table sorts quickly)
    """
    return table.item(row, 2).data(QtCore.Qt.DisplayRole)


def distances_shown(game):
    """
    {planet name: distance text, as displayed}
    """
    browser = game.locationBrowser
    table = browser.table
    return {table.item(row, 0).text(): browser.distanceDelegate.displayText(distance(table, row), QtCore.QLocale())
            for row in range(table.rowCount())}


def test_distance_column(game, no_pirates):
    state = game.state
    expected = {p.full_name: "%.1f ly" % state.home_planet.distance_to(p) for p in state.planets}
    assert distances_shown(game) == expected
    assert distances_shown(game)[state.home_planet.full_name] == "0.0 ly"

    # Distances are measured from wherever the player is
    target = state.planets[4]
    select(game, target)
    game.locationBrowser.travelButtonClicked()
    expected = {p.full_name: "%.1f ly" % target.distance_to(p) for p in state.planets}
    assert distances_shown(game) == expected


def test_sort_planets_by_distance(game, no_pirates):
    game.state.expand_planets(30)
    game.locationBrowser.update()
    table = game.locationBrowser.table
    header = table.horizontalHeader()
    QtTest.QTest.mouseClick(header.viewport(), QtCore.Qt.LeftButton,
                            pos=QtCore.QPoint(header.sectionViewportPosition(2) + 5, header.height() // 2))
    distances = [distance(table, row) for row in range(table.rowCount())]
    assert distances in (sorted(distances), sorted(distances, reverse=True))
    assert distances != [distance(table, 0)] * len(distances)

    # Travelling keeps the sort order, and colours still follow the right planets
    target = table.item(5, 0).data(QtCore.Qt.UserRole)
    select(game, target)
    game.locationBrowser.travelButtonClicked()
    distances = [distance(table, row) for row in range(table.rowCount())]
    assert distances in (sorted(distances), sorted(distances, reverse=True))
    assert shown_colours(game) == expected_colours(game)


def test_home_planet_is_bold(game):
    table = game.locationBrowser.table
    for row in range(table.rowCount()):
        is_home = table.item(row, 0).data(QtCore.Qt.UserRole) is game.state.home_planet
        assert table.item(row, 0).font().bold() == is_home
        assert bool(table.item(row, 0).toolTip()) == is_home


def test_travelling_updates_table_without_rebuilding_it(game, no_pirates):
    # Rebuilding every row after each trip was slow with thousands of planets
    table = game.locationBrowser.table
    cells = [table.item(row, 0) for row in range(table.rowCount())]
    select(game, game.state.planets[3])
    game.locationBrowser.travelButtonClicked()
    after = [table.item(row, 0) for row in range(table.rowCount())]
    assert all(any(a is c for c in cells) for a in after)
    assert distances_shown(game)[game.state.planets[3].full_name] == "0.0 ly"


def test_travel_home_selects_home_planet(game, dialogs, no_pirates):
    state = game.state
    away = state.planets[3]
    select(game, away)
    game.locationBrowser.travelButtonClicked()
    assert game.locationBrowser.selectedPlanet() is away

    game.locationBrowser.homeButtonClicked()
    assert state.current_planet is state.home_planet
    assert game.locationBrowser.selectedPlanet() is state.home_planet


def test_declined_trip_home_keeps_selection(game, dialogs, no_pirates):
    state = game.state
    away = state.planets[3]
    select(game, away)
    game.locationBrowser.travelButtonClicked()

    dialogs.answers["Travel"] = False
    game.locationBrowser.homeButtonClicked()
    assert state.current_planet is away
    assert game.locationBrowser.selectedPlanet() is away
