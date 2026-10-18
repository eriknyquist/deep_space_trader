import types

import pytest
from PyQt5 import QtCore, QtTest

from deep_space_trader import constants as const
from deep_space_trader import store
from deep_space_trader.location_picker import PlanetDestructionPicker, DONT_FIGHT
from deep_space_trader.i18n import formatDistance

from helpers import row_of, column


@pytest.fixture
def no_resistance(monkeypatch):
    monkeypatch.setattr(PlanetDestructionPicker, "checkForResistingPlanet", lambda self, planets: None)


def resisting(monkeypatch, planet):
    monkeypatch.setattr(PlanetDestructionPicker, "checkForResistingPlanet", lambda self, planets: planet)


def picker(game):
    return PlanetDestructionPicker(game, types.SimpleNamespace(price=const.PLANET_DESTRUCTION_COST))


def choose(dialog, planets):
    for planet in planets:
        dialog.table.selectRow(row_of(dialog.table, planet))


def leave_home(game):
    """
    Move the player off the home planet (which can't be destroyed), and return
    the planet they are now on
    """
    state = game.state
    state.change_current_planet(next(p for p in state.planets if p is not state.home_planet))
    return state.current_planet


def others(game, count):
    """
    Up to 'count' planets that can be destroyed, other than the current planet
    """
    state = game.state
    return [p for p in state.planets if p is not state.current_planet and p is not state.home_planet][:count]


def test_picker_columns(game):
    # Bug 17: the "Planet value" column used to show visited yes/no
    dialog = picker(game)
    table = dialog.table
    headers = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
    assert headers == ["Planet name", "Visited?", "Distance", "Planet value"]

    for row in range(table.rowCount()):
        planet = table.item(row, 0).data(QtCore.Qt.UserRole)
        assert table.item(row, 0).text() == planet.full_name
        assert table.item(row, 1).text() == ("yes" if planet.visited else "no")
        distance = game.state.current_planet.distance_to(planet)
        assert table.item(row, 2).data(QtCore.Qt.DisplayRole) == pytest.approx(distance)
        assert shown_text(table, row, 2) == formatDistance(distance)
        assert table.item(row, 3).text() == "{:,}".format(int(game.state.shown_market_value(planet)))


def test_picker_sorts_by_value(game):
    game.state.expand_planets(20)
    table = picker(game).table
    table.sortItems(3)
    values = [table.item(row, 3).value for row in range(table.rowCount())]
    assert values == sorted(values)


def test_picker_sorts_by_distance(game):
    game.state.expand_planets(20)
    table = picker(game).table
    table.sortItems(2)
    current = game.state.current_planet
    planets = [table.item(row, 0).data(QtCore.Qt.UserRole) for row in range(table.rowCount())]
    distances = [current.distance_to(p) for p in planets]
    # Sorted as numbers, not as text ("100 ly" would come before "9 ly")
    assert distances == sorted(distances)


def shown_text(table, row, column):
    index = table.model().index(row, column)
    delegate = table.itemDelegateForColumn(column)
    return delegate.displayText(index.data(), QtCore.QLocale())


def test_destroy_selected_after_sorting(game, no_resistance):
    # Bug 14: after sorting, the wrong planets were destroyed
    dialog = picker(game)
    dialog.table.sortItems(0, QtCore.Qt.DescendingOrder)
    victim = others(game, 1)[0]
    choose(dialog, [victim])
    dialog.selectButtonClicked()
    assert victim not in game.state.planets
    assert len(game.state.planets) == const.INITIAL_PLANET_COUNT - 1


def test_destroy_several_planets(game, dialogs, no_resistance):
    state = game.state
    victims = others(game, 3)
    items = sum(p.items.count() for p in victims)
    dialog = picker(game)
    choose(dialog, victims)
    assert dialog.selectButton.text() == "Destroy selected (cost {:,})".format(3 * const.PLANET_DESTRUCTION_COST)

    dialog.selectButtonClicked()
    names = [p.full_name for p in victims]
    assert not any(p in state.planets for p in victims)
    assert state.warehouse.count() == items
    assert dialog.accepted
    assert dialog.final_price == 3 * const.PLANET_DESTRUCTION_COST
    assert dialogs.messages("question")[0].startswith(
        "Are you sure you want to destroy %s, %s and %s?" % tuple(names))
    assert dialogs.messages("info") == ["Destruction of %s, %s and %s is complete." % tuple(names)]
    assert game.locationBrowser.table.rowCount() == len(state.planets)


def test_destroy_many_planets(game, dialogs, no_resistance):
    game.state.expand_planets(10)
    dialog = picker(game)
    choose(dialog, others(game, 7))
    dialog.selectButtonClicked()
    assert dialogs.messages("info") == ["Destruction of 7 planets is complete."]


def test_destroy_nothing_selected(game, dialogs):
    picker(game).selectButtonClicked()
    assert dialogs.messages("error") == ["Please select planets to destroy first!"]


def test_destroy_own_planet_kills_player(game, dialogs, no_resistance):
    leave_home(game)
    dialog = picker(game)
    choose(dialog, [game.state.current_planet])
    dialog.selectButtonClicked()
    assert "so you will also die" in dialogs.messages("question")[0]
    assert dialog.died
    assert dialogs.titles("info")[-1] == "Dead!"


def test_selected_planets_cost_more_than_money(game):
    game.state.money = const.PLANET_DESTRUCTION_COST
    dialog = picker(game)
    choose(dialog, others(game, 2))
    assert not dialog.selectButton.isEnabled()


def test_declining_to_fight_the_only_selected_planet(game, dialogs, monkeypatch):
    # Bug 3: this used to crash
    victim = others(game, 1)[0]
    resisting(monkeypatch, victim)
    dialogs.choices["Planet is resisting!"] = DONT_FIGHT
    dialog = picker(game)
    choose(dialog, [victim])
    dialog.selectButtonClicked()

    assert victim in game.state.planets
    assert victim.resists_destruction
    assert not dialog.accepted
    assert dialogs.titles("info") == ["Chickened out!"]


def test_declining_to_fight_own_planet(game, dialogs, monkeypatch):
    # Bug 19: you used to die even though your planet wasn't destroyed
    state = game.state
    home = leave_home(game)
    victim = others(game, 1)[0]
    resisting(monkeypatch, home)
    dialogs.choices["Planet is resisting!"] = DONT_FIGHT
    dialog = picker(game)
    choose(dialog, [home, victim])
    dialog.selectButtonClicked()

    assert home in state.planets
    assert victim not in state.planets
    assert not dialog.died
    assert "Dead!" not in dialogs.titles("info")
    assert dialog.final_price == const.PLANET_DESTRUCTION_COST


def test_fight_and_win_against_resisting_planet(game, dialogs, monkeypatch):
    state = game.state
    victim = others(game, 1)[0]
    resisting(monkeypatch, victim)
    monkeypatch.setattr(state, "battle_won", lambda: True)
    state.battle_level = 0       # every battle costs 70-90 health at level 0
    dialog = picker(game)
    choose(dialog, [victim])
    dialog.selectButtonClicked()

    assert victim not in state.planets
    assert state.health < 100
    assert not dialog.died
    assert dialogs.titles("info")[0] == "Victory!"


def test_fight_and_lose_against_resisting_planet(game, dialogs, monkeypatch):
    victim = others(game, 1)[0]
    resisting(monkeypatch, victim)
    monkeypatch.setattr(game.state, "battle_won", lambda: False)
    dialog = picker(game)
    choose(dialog, [victim])
    dialog.selectButtonClicked()

    assert dialog.died
    assert victim in game.state.planets
    assert dialogs.titles("info") == ["Defeat!"]


def test_a_planet_that_resisted_resists_again(game):
    planets = others(game, 3)
    planets[1].resists_destruction = True
    assert picker(game).checkForResistingPlanet(planets) is planets[1]


def test_resistance_is_certain_with_many_planets(game):
    game.state.expand_planets(20)
    planets = others(game, 20)
    dialog = picker(game)
    assert all(dialog.checkForResistingPlanet(planets) in planets for _ in range(20))


def test_destroy_all(game, dialogs, no_resistance):
    state = game.state
    home = state.current_planet
    destroyed = others(game, 100)
    items = sum(p.items.count() for p in destroyed)
    dialog = picker(game)
    assert dialog.allButton.text() == "Destroy all (cost {:,})".format(
        (len(state.planets) - 1) * const.PLANET_DESTRUCTION_COST)

    dialog.allButtonClicked()
    assert state.planets == [home]
    assert state.warehouse.count() == items
    assert dialog.final_price == len(destroyed) * const.PLANET_DESTRUCTION_COST
    assert dialogs.messages("info") == ["Destruction of all planets is complete."]
    assert column(game.locationBrowser.table, 0) == [home.full_name]


def test_destroy_all_keeps_a_planet_that_resisted(game, dialogs, monkeypatch):
    state = game.state
    survivor = others(game, 1)[0]
    resisting(monkeypatch, survivor)
    dialogs.choices["Planet is resisting!"] = DONT_FIGHT
    dialog = picker(game)
    dialog.allButtonClicked()
    assert state.planets == [state.current_planet, survivor]
    assert dialog.final_price == (const.INITIAL_PLANET_COUNT - 2) * const.PLANET_DESTRUCTION_COST


def test_destroy_all_with_nothing_destroyed(game, dialogs, monkeypatch):
    # Bug 20: this used to count as a purchase and report success
    state = game.state
    state.planets = state.planets[:2]
    survivor = state.planets[1]
    resisting(monkeypatch, survivor)
    dialogs.choices["Planet is resisting!"] = DONT_FIGHT
    dialog = picker(game)
    dialog.allButtonClicked()
    assert not dialog.accepted
    assert state.planets == [state.current_planet, survivor]
    assert "Success" not in dialogs.titles("info")


def test_destroy_all_disabled_without_enough_money(game):
    game.state.money = const.PLANET_DESTRUCTION_COST
    assert not picker(game).allButton.isEnabled()


def test_destroy_all_disabled_with_one_planet(game):
    game.state.planets = [game.state.current_planet]
    assert not picker(game).allButton.isEnabled()


def test_destruction_keeps_planet_search(game, no_resistance):
    # Bug 5 (second part): rows used to be removed by their position in the full list
    state = game.state
    shown = state.planets[-1]
    QtTest.QTest.keyClicks(game.locationBrowser.planetSearchText, shown.full_name)
    victim = next(p for p in others(game, 100) if p is not shown)
    dialog = picker(game)
    choose(dialog, [victim])
    dialog.selectButtonClicked()
    assert column(game.locationBrowser.table, 0) == [shown.full_name]


def test_buying_the_destruction_kit(game, dialogs, no_resistance):
    state = game.state
    victims = others(game, 2)
    money = state.money

    def destroy(dialog):
        choose(dialog, victims)
        dialog.selectButtonClicked()

    dialogs.on_exec = destroy
    shop = store.Store(game)
    shop.buyItem(next(i for i in store.store_items if isinstance(i, store.PlanetDestruction)))
    assert not any(p in state.planets for p in victims)
    assert state.money == money - 2 * const.PLANET_DESTRUCTION_COST
    assert state.store_purchases == 1


def test_destroying_own_planet_from_the_store_ends_the_game(game, dialogs, no_resistance):
    state = game.state
    home = leave_home(game)

    def destroy(dialog):
        choose(dialog, [home])
        dialog.selectButtonClicked()

    dialogs.on_exec = destroy
    shop = store.Store(game)
    shop.buyItem(next(i for i in store.store_items if isinstance(i, store.PlanetDestruction)))
    assert home not in state.planets
    assert state.day == 1
    assert len(state.planets) == const.INITIAL_PLANET_COUNT
    assert state.store_purchases == 0


# ----- The home planet can't be destroyed -----

def test_home_planet_is_not_in_the_picker(game):
    leave_home(game)
    dialog = picker(game)
    shown = [dialog.table.item(row, 0).data(QtCore.Qt.UserRole) for row in range(dialog.table.rowCount())]
    assert game.state.home_planet not in shown
    assert game.state.current_planet in shown
    assert len(shown) == len(game.state.planets) - 1


def test_destroy_all_away_from_home_spares_home(game, dialogs, no_resistance):
    state = game.state
    current = leave_home(game)
    destroyed = others(game, 100)
    dialog = picker(game)
    assert dialog.all_planets_cost == len(destroyed) * const.PLANET_DESTRUCTION_COST
    assert len(destroyed) == const.INITIAL_PLANET_COUNT - 2

    dialog.allButtonClicked()
    assert state.planets == [state.home_planet, current]
    assert "All planets except for your home planet and the one you are currently on" in \
        dialogs.messages("question")[0]


def test_destroy_all_disabled_with_only_home_and_current_planet(game):
    state = game.state
    current = leave_home(game)
    state.planets = [state.home_planet, current]
    dialog = picker(game)
    assert not dialog.allButton.isEnabled()
    assert dialog.allButton.text() == "Destroy all"


class RecordingProgress(object):
    """
    Stand-in for utils.ProgressWindow, recording what it's told
    """
    made = []

    def __init__(self, parent, text, delay_ms=300):
        self.text = text
        self.done = []
        self.finished = False
        RecordingProgress.made.append(self)

    def progress(self, fraction):
        self.done.append(fraction)

    def finish(self):
        self.finished = True

    def deleteLater(self):
        pass


def test_progress_bar_while_loading_planets(game, monkeypatch):
    from deep_space_trader import location_picker
    monkeypatch.setattr(location_picker, "ProgressWindow", RecordingProgress)
    RecordingProgress.made = []

    state = game.state
    state.scout_level = 3
    state.expand_planets(3000)
    state.day = 10
    picker(game)

    assert len(RecordingProgress.made) == 1
    progress = RecordingProgress.made[0]
    assert progress.text == "Loading planet information..."
    assert progress.finished
    # Goes up steadily, through catching up and filling the table
    assert progress.done == sorted(progress.done)
    assert len(progress.done) > 5
    assert progress.done[-1] >= 0.9


def test_progress_window(qapp):
    from PyQt5 import QtWidgets
    from deep_space_trader.utils import ProgressWindow

    window = ProgressWindow(None, "Loading planet information...", delay_ms=0)
    assert window.labelText() == "Loading planet information..."
    assert window.windowTitle() == "Please wait"
    assert window.findChild(QtWidgets.QPushButton) is None   # can't be cancelled

    window.progress(0.25)
    assert window.value() == 250
    window.progress(0.1)   # never goes backwards
    assert window.value() == 250
    window.reject()        # Escape does nothing
    window.finish()
    assert not window.isVisible()


def check_progress(progress, text):
    assert progress.text == text
    assert progress.finished
    assert progress.done == sorted(progress.done)
    assert progress.done[-1] >= 0.99


@pytest.fixture
def recorded_progress(monkeypatch):
    from deep_space_trader import location_picker
    monkeypatch.setattr(location_picker, "ProgressWindow", RecordingProgress)
    monkeypatch.setattr(store, "ProgressWindow", RecordingProgress)
    RecordingProgress.made = []
    return RecordingProgress.made


def test_progress_bar_while_destroying_selected_planets(game, dialogs, recorded_progress, monkeypatch):
    monkeypatch.setattr(PlanetDestructionPicker, "checkForResistingPlanet", lambda self, planets: None)
    dialog = picker(game)
    victims = others(game, 3)
    choose(dialog, victims)
    dialog.selectButtonClicked()

    # Loading the window, then destroying
    assert [p.text for p in recorded_progress] == ["Loading planet information...", "Destroying planets..."]
    check_progress(recorded_progress[1], "Destroying planets...")
    assert not any(p in game.state.planets for p in victims)


def test_progress_bar_while_destroying_all_planets(game, dialogs, recorded_progress, monkeypatch):
    monkeypatch.setattr(PlanetDestructionPicker, "checkForResistingPlanet", lambda self, planets: None)
    state = game.state
    picker(game).allButtonClicked()
    check_progress(recorded_progress[-1], "Destroying planets...")
    assert state.planets == [state.home_planet]


def test_progress_bar_while_exploring(game, dialogs, recorded_progress):
    state = game.state
    state.scout_level = 1
    before = len(state.planets)
    item = next(i for i in store.store_items if isinstance(i, store.PlanetExploration))
    item.use()

    assert len(state.planets) > before
    assert len(recorded_progress) == 1
    check_progress(recorded_progress[0], "Exploring new planets...")


def test_destroying_many_planets_keeps_the_others_in_order(game, dialogs, monkeypatch):
    monkeypatch.setattr(PlanetDestructionPicker, "checkForResistingPlanet", lambda self, planets: None)
    state = game.state
    state.scout_level = 3
    state.expand_planets(200)
    victims = others(game, 150)[::2]
    survivors = [p for p in state.planets if p not in victims]

    dialog = picker(game)
    choose(dialog, victims)
    dialog.selectButtonClicked()
    assert state.planets == survivors
