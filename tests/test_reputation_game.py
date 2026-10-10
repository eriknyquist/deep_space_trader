"""
Reputation in the game: what changes it, and what it changes
"""
import time

import pytest
from PyQt5 import QtCore, QtGui

from deep_space_trader import constants as const
from deep_space_trader import reputation
from deep_space_trader.transaction_dialogs import Buy, Sell
from deep_space_trader.location_browser import TradingConsole
from deep_space_trader.item_browsers import TradingConsolePlanetDisplay

from helpers import give, row_of
from deep_space_trader.location_picker import PlanetDestructionPicker
from test_destruction import picker, choose, others, resisting
from test_trading import planet_item, untraded_item, select


@pytest.fixture
def no_resistance(monkeypatch):
    monkeypatch.setattr(PlanetDestructionPicker, "checkForResistingPlanet", lambda self, planets: None)


def reputation_at(state, planet):
    # Works for destroyed planets too, since it only uses the position
    return float(state.reputation.at([planet.x], [planet.y])[0])


@pytest.fixture
def spy(game, monkeypatch):
    """
    Records the reputation events the game reports, as (event name, argument)
    """
    calls = []
    state = game.state
    for name in ("planets_destroyed", "fought_resisting_planet", "sold_to", "sample_accepted"):
        original = getattr(state, name)

        def record(arg, name=name, original=original):
            calls.append((name, arg))
            original(arg)

        monkeypatch.setattr(state, name, record)

    return calls


def set_reputation(game, monkeypatch, value):
    monkeypatch.setattr(game.state, "reputation_of", lambda planet: value)


# ----- Events -----

def test_destroying_selected_planets(game, spy, no_resistance):
    victims = others(game, 2)
    dialog = picker(game)
    choose(dialog, victims)
    dialog.selectButtonClicked()

    assert spy == [("planets_destroyed", victims)]
    assert all(reputation_at(game.state, v) < const.STARTING_REPUTATION - 10 for v in victims)


def test_destroying_all_planets(game, spy, no_resistance):
    victims = others(game, 100)
    picker(game).allButtonClicked()
    assert spy == [("planets_destroyed", victims)]


def test_cancelled_destruction_changes_nothing(game, dialogs, spy):
    dialogs.answers["Are you sure?"] = False
    dialog = picker(game)
    choose(dialog, others(game, 1))
    dialog.selectButtonClicked()
    dialog.allButtonClicked()
    assert spy == []


@pytest.mark.parametrize("won", [True, False])
def test_fighting_a_resisting_planet(game, spy, monkeypatch, won):
    victim = others(game, 1)[0]
    resisting(monkeypatch, victim)
    monkeypatch.setattr(game.state, "battle_won", lambda: won)
    dialog = picker(game)
    choose(dialog, [victim])
    dialog.selectButtonClicked()

    names = [name for name, arg in spy]
    assert ("fought_resisting_planet", victim) in spy
    assert ("planets_destroyed" in names) == won


def test_declining_to_fight_is_not_a_fight(game, dialogs, spy, monkeypatch):
    victim = others(game, 1)[0]
    resisting(monkeypatch, victim)
    dialogs.answers["Planet is resisting!"] = False
    dialog = picker(game)
    choose(dialog, [victim])
    dialog.selectButtonClicked()
    assert spy == []


def test_selling(game, spy):
    name = planet_item(game)
    give(game.state.items, name, 10)
    dialog = Sell(game, name)
    dialog.spinbox.setValue(5)
    dialog.acceptButtonClicked()
    assert spy == [("sold_to", game.state.current_planet)]
    assert game.state.reputation_of(game.state.current_planet) > const.STARTING_REPUTATION


def test_sell_all(game, spy):
    name = planet_item(game)
    give(game.state.items, name, 10)
    game.playerItemBrowser.sellAllButtonClicked()
    assert spy == [("sold_to", game.state.current_planet)]


def test_buying_is_not_an_event(game, spy):
    dialog = Buy(game, planet_item(game))
    dialog.spinbox.setValue(5)
    dialog.acceptButtonClicked()
    assert spy == []


@pytest.mark.parametrize("accepted", [True, False])
def test_free_sample(game, spy, monkeypatch, accepted):
    name = untraded_item(game)
    give(game.state.items, name, 20)
    select(game.playerItemBrowser, name)
    monkeypatch.setattr(const, "ITEM_SAMPLE_SUCCESS_PERCENT", 100 if accepted else 0)
    game.playerItemBrowser.sellButtonClicked()
    assert spy == ([("sample_accepted", game.state.current_planet)] if accepted else [])


# ----- Prices -----

@pytest.mark.parametrize("reputation", [0, 40, 100])
def test_buy_dialog_uses_reputation_price(game, monkeypatch, reputation):
    state = game.state
    set_reputation(game, monkeypatch, reputation)
    name = planet_item(game)
    cost = state.buy_total(state.current_planet, name, 10)
    money = state.money

    dialog = Buy(game, name)
    dialog.spinbox.setValue(10)
    assert dialog.spinboxLabel.text() == "Buy quantity (cost: {:,})".format(cost)
    dialog.acceptButtonClicked()
    assert state.money == money - cost
    assert state.transaction_log[-1][-1] == pytest.approx(cost / 10.0)


def test_cheap_items_cost_more_in_total(game, monkeypatch):
    state = game.state
    set_reputation(game, monkeypatch, 56)      # prices 10% worse
    name = planet_item(game)
    state.current_planet.items.items[name].value = 4
    state.capacity = 10 ** 6
    money = state.money

    dialog = Buy(game, name)
    dialog.spinbox.setValue(1000)
    assert dialog.spinboxLabel.text() == "Buy quantity (cost: 4,400)"
    dialog.acceptButtonClicked()
    assert state.money == money - 4400
    assert "bought 1,000 %s for 4.40 each" % name in state.read_transaction_log()


def test_buy_max_uses_reputation_price(game, monkeypatch):
    state = game.state
    set_reputation(game, monkeypatch, 0)
    name = planet_item(game)
    state.money = state.buy_total(state.current_planet, name, 7) + 1
    dialog = Buy(game, name)
    dialog.maxButtonClicked()
    assert dialog.spinbox.value() == 7


@pytest.mark.parametrize("reputation", [20, 100])
def test_sell_dialog_uses_reputation_price(game, monkeypatch, reputation):
    state = game.state
    set_reputation(game, monkeypatch, reputation)
    name = planet_item(game)
    gain = state.sell_total(state.current_planet, name, 10)
    give(state.items, name, 10)
    money = state.money

    dialog = Sell(game, name)
    dialog.spinbox.setValue(10)
    assert dialog.spinboxLabel.text() == "Sell quantity (gain: {:,})".format(gain)
    dialog.acceptButtonClicked()
    assert state.money == money + gain


def test_sell_all_uses_reputation_price(game, dialogs, monkeypatch):
    state = game.state
    set_reputation(game, monkeypatch, 30)
    name = planet_item(game)
    state.current_planet.items.items[name].value = 4
    gain = state.sell_total(state.current_planet, name, 1000)
    assert gain < 4000
    give(state.items, name, 1000)
    money = state.money

    game.playerItemBrowser.sellAllButtonClicked()
    assert "(total gain: {:,})".format(gain) in dialogs.messages("question")[0]
    assert state.money == money + gain


@pytest.mark.parametrize("value", [0, 100])
def test_tables_show_normal_prices(game, monkeypatch, value):
    # Reputation only changes prices in the Buy and Sell dialogs (and Sell all)
    state = game.state
    set_reputation(game, monkeypatch, value)
    name = planet_item(game)
    game.planetItemBrowser.update()

    item = state.current_planet.items.items[name]
    delta = (item.value - item.type.base_value) / (item.type.base_value / 100.0)
    table = game.planetItemBrowser.table
    row = row_of(table, name)
    assert table.item(row, 2).value == item.value
    assert table.item(row, 3).value == pytest.approx(delta)

    display = TradingConsole(game, state.current_planet).findChild(TradingConsolePlanetDisplay)
    assert display.table.item(row_of(display.table, name), 2).value == item.value


# ----- Price messages in the Buy and Sell dialogs, and Sell all -----

def price_dialog(game, monkeypatch, cls, value, quantity):
    state = game.state
    set_reputation(game, monkeypatch, value)
    name = planet_item(game)
    state.current_planet.items.items[name].value = 1000
    give(state.items, name, 10)
    dialog = cls(game, name)
    if quantity:
        dialog.spinbox.setValue(quantity)
    return dialog, name


@pytest.mark.parametrize("cls, value, text", [
    (Buy, 100, "{0} would normally charge 10,000 for this much {1}, but they're willing to sell it to you "
               "for 9,000 because of your shining reputation! Well done!"),
    (Buy, 0, "{0} would normally charge 10,000 for this much {1}, but they're charging you 15,000, "
             "because they don't trust you."),
    (Sell, 100, "{0} would normally pay 10,000 for this much {1}, but they're willing to pay you 11,000 "
                "because of your shining reputation! Well done!"),
    (Sell, 0, "{0} would normally pay 10,000 for this much {1}, but they'll only pay you 5,000, "
              "because they don't trust you."),
])
def test_dialogs_explain_reputation_prices(game, monkeypatch, cls, value, text):
    dialog, name = price_dialog(game, monkeypatch, cls, value, 10)
    assert not dialog.reputationLabel.isHidden()
    assert dialog.reputationLabel.text() == text.format(game.state.current_planet.full_name, name)

    # Green for better prices, red for worse
    color = reputation.GOOD_PRICE_COLOR if value > const.STARTING_REPUTATION else reputation.BAD_PRICE_COLOR
    assert dialog.reputationLabel.styleSheet() == "QLabel { color: %s; }" % color


@pytest.mark.parametrize("cls, value, text", [
    (Buy, 100, "for 2,700 because"),
    (Sell, 0, "only pay you 1,500,"),
])
def test_dialog_message_follows_quantity(game, monkeypatch, cls, value, text):
    dialog, name = price_dialog(game, monkeypatch, cls, value, 0)
    # No message before a quantity is chosen
    assert dialog.spinbox.value() == 0
    assert dialog.reputationLabel.isHidden()

    dialog.spinbox.setValue(3)
    assert not dialog.reputationLabel.isHidden()
    assert " 3,000 for this much" in dialog.reputationLabel.text()
    assert text in dialog.reputationLabel.text()

    dialog.spinbox.setValue(0)
    assert dialog.reputationLabel.isHidden()


@pytest.mark.parametrize("cls", [Buy, Sell])
def test_no_message_at_normal_prices(game, monkeypatch, cls):
    dialog, name = price_dialog(game, monkeypatch, cls, const.STARTING_REPUTATION, 10)
    assert dialog.reputationLabel.isHidden()


@pytest.mark.parametrize("value, text", [
    (100, "{0} would normally pay 10,000 for these items, but they're willing to pay you 11,000 "
          "because of your shining reputation! Well done!"),
    (20, "{0} would normally pay 10,000 for these items, but they'll only pay you 6,429, "
         "because they don't trust you."),
    (const.STARTING_REPUTATION, None),
])
def test_sell_all_explains_reputation_prices(game, dialogs, monkeypatch, value, text):
    price_dialog(game, monkeypatch, Sell, value, 0)
    game.playerItemBrowser.sellAllButtonClicked()
    question = dialogs.messages("question")[0]
    if text is None:
        assert "<br><br>" not in question
    else:
        color = reputation.GOOD_PRICE_COLOR if value > const.STARTING_REPUTATION else reputation.BAD_PRICE_COLOR
        assert question.endswith('<br><br><span style="color: %s;">%s</span>' % (
            color, text.format(game.state.current_planet.full_name)))


# ----- Refusing to trade -----

@pytest.fixture
def refusing(game, monkeypatch):
    set_reputation(game, monkeypatch, const.REFUSE_TRADE_REPUTATION - 1)
    return "%s refuses to trade with you, because of what you've done nearby." % game.state.current_planet.full_name


def test_refuses_to_sell_to_you(game, dialogs, refusing):
    select(game.planetItemBrowser, planet_item(game))
    game.planetItemBrowser.buyButtonClicked()
    assert dialogs.messages("error") == [refusing]
    assert dialogs.titles("error") == ["Trade refused"]
    assert dialogs.executed == []


def test_refuses_to_buy_from_you(game, dialogs, refusing):
    state = game.state
    name = planet_item(game)
    give(state.items, name, 10)
    select(game.playerItemBrowser, name)
    money = state.money

    game.playerItemBrowser.sellButtonClicked()
    game.playerItemBrowser.sellAllButtonClicked()
    assert dialogs.messages("error") == [refusing, refusing]
    assert dialogs.executed == []
    assert state.items.items[name].quantity == 10
    assert state.money == money


def test_refuses_free_samples(game, dialogs, refusing):
    name = untraded_item(game)
    give(game.state.items, name, 20)
    select(game.playerItemBrowser, name)
    game.playerItemBrowser.sellButtonClicked()
    assert dialogs.messages() == [refusing]
    assert game.state.items.items[name].quantity == 20


def test_double_clicks_are_refused_too(game, dialogs, refusing):
    name = planet_item(game)
    give(game.state.items, name, 10)
    select(game.planetItemBrowser, name)
    select(game.playerItemBrowser, name)
    game.planetItemBrowser.onDoubleClick(None)
    game.playerItemBrowser.onDoubleClick(None)
    assert dialogs.messages("error") == [refusing, refusing]


def test_trades_just_above_refusal(game, dialogs, monkeypatch):
    set_reputation(game, monkeypatch, const.REFUSE_TRADE_REPUTATION)
    select(game.planetItemBrowser, planet_item(game))
    game.planetItemBrowser.buyButtonClicked()
    assert [type(d) for d in dialogs.executed] == [Buy]


def test_trading_console_still_shows_prices(game, refusing):
    planet = game.state.current_planet
    console = TradingConsole(game, planet)
    display = console.findChild(TradingConsolePlanetDisplay)
    assert display.table.rowCount() == len(planet.items.items)


# ----- Info bar -----

@pytest.mark.parametrize("value, color, tooltip", [
    (100, "#00c853", "Reputation here: Allied (100). Prices are 10% better."),
    (70, "#9ccc3c", "Reputation here: Friendly (70). Prices are normal."),
    (69.9, "#9ccc3c", "Reputation here: Friendly (70). Prices are normal."),
    (69.4, "#ffd600", "Reputation here: Wary (69). Prices are normal."),
    (56, "#ffd600", "Reputation here: Wary (56). Prices are 10% worse."),
    (20, "#ff8f00", "Reputation here: Hostile (20). Prices are 36% worse."),
])
def test_info_bar_reputation(game, monkeypatch, value, color, tooltip):
    set_reputation(game, monkeypatch, value)
    game.infoBar.update()
    assert game.infoBar.reputationBar.value() == int(round(value))
    assert color in game.infoBar.reputationBar.styleSheet()
    assert game.infoBar.reputationGroup.toolTip() == tooltip


def test_info_bar_when_planet_refuses_to_trade(game, monkeypatch):
    set_reputation(game, monkeypatch, 3)
    game.infoBar.update()
    assert "#e53935" in game.infoBar.reputationBar.styleSheet()
    assert game.infoBar.reputationGroup.toolTip() == \
        "Reputation here: Refuses to trade (3). %s refuses to trade with you." % game.state.current_planet.full_name


def test_info_bar_follows_selling(game):
    name = planet_item(game)
    give(game.state.items, name, 10)
    game.playerItemBrowser.sellAllButtonClicked()
    assert game.infoBar.reputationBar.value() == round(game.state.reputation_of(game.state.current_planet))
    assert game.infoBar.reputationBar.value() > const.STARTING_REPUTATION


def test_info_bar_reputation_tooltip_can_be_turned_off(game):
    game.infoBar.enableTooltips(False)
    assert game.infoBar.reputationGroup.toolTip() == ""


def test_reputation_bar_draws(game):
    image = game.infoBar.reputationBar.grab()
    assert not image.isNull()


# ----- Planets table -----

def planets_table_cell(game, planet, col):
    table = game.locationBrowser.table
    return table.item(row_of(table, planet), col)


def test_planets_table_reputation_column(game):
    from deep_space_trader.location_browser import REPUTATION_COLUMN
    table = game.locationBrowser.table
    assert table.horizontalHeaderItem(REPUTATION_COLUMN).text() == "Reputation"

    state = game.state
    victim, near = others(game, 2)
    near.x, near.y = victim.x + 3, victim.y
    state.planets_destroyed([victim])
    game.locationBrowser.update()

    value = state.reputation_of(near)
    cell = planets_table_cell(game, near, REPUTATION_COLUMN)
    assert cell.data(QtCore.Qt.DisplayRole) == pytest.approx(value, abs=0.005)
    shown = game.locationBrowser.reputationDelegate.displayText(cell.data(QtCore.Qt.DisplayRole), QtCore.QLocale())
    assert shown == "%s (%d)" % (reputation.levelName(value), round(value))


def test_planets_table_sorts_by_reputation(game):
    from deep_space_trader.location_browser import REPUTATION_COLUMN
    state = game.state
    state.expand_planets(30)
    state.planets_destroyed(others(game, 3))
    game.locationBrowser.update()

    table = game.locationBrowser.table
    table.sortItems(REPUTATION_COLUMN)
    values = [table.item(row, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole) for row in range(table.rowCount())]
    assert values == sorted(values)
    assert values[0] < values[-1]


def test_planets_table_reputation_follows_travel_and_selling(game, dialogs, monkeypatch):
    from deep_space_trader.location_browser import REPUTATION_COLUMN
    state = game.state
    monkeypatch.setattr(state, "pirate_chance", lambda planet: 0)
    destination = others(game, 1)[0]
    state.planets_destroyed([destination])
    game.locationBrowser.update()
    low = planets_table_cell(game, destination, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole)

    # A day passes, so reputation recovers a little
    game.locationBrowser.travelToPlanet(destination)
    assert state.current_planet is destination
    after_travel = planets_table_cell(game, destination, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole)
    assert after_travel > low

    name = planet_item(game)
    give(state.items, name, 10)
    game.playerItemBrowser.sellAllButtonClicked()
    after_sale = planets_table_cell(game, destination, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole)
    assert after_sale == pytest.approx(state.reputation_of(destination), abs=0.005)
    assert after_sale > after_travel


def test_planets_table_refresh_is_fast_with_many_planets(game):
    game.state.expand_planets(20000 - len(game.state.planets))
    game.locationBrowser.update()

    start = time.time()
    game.locationBrowser.refreshReputations()
    assert time.time() - start < 2


def test_planets_table_reputation_follows_next_day_button(game, monkeypatch):
    from deep_space_trader.location_browser import REPUTATION_COLUMN
    monkeypatch.setattr(game, "runRandomNotifications", lambda: None)
    state = game.state
    victim = others(game, 1)[0]
    state.planets_destroyed([victim])
    game.locationBrowser.update()
    before = planets_table_cell(game, victim, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole)

    game.buttonBar.dayButtonClicked()
    after = planets_table_cell(game, victim, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole)
    assert after > before
    assert after == pytest.approx(state.reputation_of(victim), abs=0.005)


def test_reputation_refresh_skips_unchanged_reputations(game, monkeypatch):
    from deep_space_trader.location_browser import REPUTATION_COLUMN
    browser = game.locationBrowser
    state = game.state
    set_cells = []
    original = browser.table.setItem
    monkeypatch.setattr(browser.table, "setItem", lambda row, col, item: (set_cells.append(col),
                                                                         original(row, col, item)))

    # Nothing has happened, so a new day changes nothing
    state.next_day()
    browser.refreshReputations()
    assert set_cells == []

    # Only planets near an event change
    near, far = others(game, 2)
    far.x, far.y = near.x + 300, near.y
    state.planets_destroyed([near])
    browser.refreshReputations()
    assert 0 < set_cells.count(REPUTATION_COLUMN) < len(state.planets)
    assert planets_table_cell(game, far, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole) == \
        const.STARTING_REPUTATION

    # Refreshing again without any change does nothing
    set_cells.clear()
    browser.refreshReputations()
    assert set_cells == []


def test_new_game_resets_planets_table_reputations(game):
    from deep_space_trader.location_browser import REPUTATION_COLUMN
    game.state.planets_destroyed(others(game, 3))
    game.locationBrowser.update()
    game.reset()
    table = game.locationBrowser.table
    assert all(table.item(row, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole) == const.STARTING_REPUTATION
               for row in range(table.rowCount()))


@pytest.mark.parametrize("search", ["", "a"])
def test_reputation_refresh_after_sorting_and_filtering(game, search):
    from deep_space_trader.location_browser import REPUTATION_COLUMN, DISTANCE_COLUMN
    state = game.state
    state.expand_planets(40)
    browser = game.locationBrowser
    browser.planetSearchText.setText(search)
    browser.update()
    table = browser.table

    for sort_column in (0, REPUTATION_COLUMN, DISTANCE_COLUMN):
        table.sortItems(sort_column, QtCore.Qt.DescendingOrder)
        state.planets_destroyed(others(game, 40)[sort_column::7])
        browser.refreshReputations()
        state.next_day()
        browser.refreshDistances()

        assert table.rowCount() == len(browser.filteredPlanets())
        for row in range(table.rowCount()):
            planet = table.item(row, 0).data(QtCore.Qt.UserRole)
            shown = table.item(row, REPUTATION_COLUMN).data(QtCore.Qt.DisplayRole)
            assert shown == pytest.approx(state.reputation_of(planet), abs=0.005)
            assert table.item(row, DISTANCE_COLUMN).data(QtCore.Qt.DisplayRole) == \
                pytest.approx(state.current_planet.distance_to(planet))

    # The current planet is still coloured, wherever it has moved to
    row = browser.rowOf(state.current_planet)
    if row is not None:
        assert table.item(row, 0).background().color() == QtGui.QColor(0, 0xAA, 0)
