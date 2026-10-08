import pytest
from PyQt5 import QtCore, QtTest

from deep_space_trader import constants as const
from deep_space_trader.price_graph import PriceHistoryGraph
from deep_space_trader.transaction_dialogs import Buy, Sell, DumpPlayerItem
from deep_space_trader.item_browsers import selectedItemName

from helpers import give, row_of, column


def planet_item(game):
    """
    Name of an item for sale on the current planet, with plenty in stock
    """
    planet = game.state.current_planet
    name = max(planet.items.items, key=lambda n: planet.items.items[n].quantity)
    planet.items.items[name].quantity = 10 ** 6
    return name


def untraded_item(game):
    """
    Name of an item that the current planet doesn't trade
    """
    game.state.current_planet.items.items.pop("antimatter", None)
    return "antimatter"


def select(browser, itemname):
    browser.update()
    browser.table.setCurrentCell(row_of(browser.table, itemname), 0)


def test_buy(game):
    state = game.state
    name = planet_item(game)
    price = state.current_planet.items.items[name].value
    money = state.money

    dialog = Buy(game, name)
    dialog.spinbox.setValue(30)
    assert dialog.spinboxLabel.text() == "Buy quantity (cost: {:,})".format(30 * price)
    dialog.acceptButtonClicked()

    assert state.items.items[name].quantity == 30
    assert state.current_planet.items.items[name].quantity == 10 ** 6 - 30
    assert state.money == money - 30 * price
    assert game.playerItemBrowserGroup.title() == "Items on your ship (30/%d)" % state.capacity
    assert "Day 1: %s, bought 30 %s for %d each" % (state.current_planet.full_name, name, price) == \
        state.read_transaction_log()
    assert game.audio.played == ["WhooshPopSound"]


def test_buy_is_limited_by_free_space(game):
    name = planet_item(game)
    give(game.state.items, "antimatter", 40)
    dialog = Buy(game, name)
    dialog.maxButtonClicked()
    assert dialog.spinbox.value() == game.state.capacity - 40


def test_buy_is_limited_by_money(game):
    name = planet_item(game)
    price = game.state.current_planet.items.items[name].value
    game.state.money = price * 7 + 1
    dialog = Buy(game, name)
    dialog.maxButtonClicked()
    assert dialog.spinbox.value() == 7


def test_buy_is_limited_by_planet_stock(game):
    name = planet_item(game)
    game.state.current_planet.items.items[name].quantity = 3
    dialog = Buy(game, name)
    dialog.maxButtonClicked()
    assert dialog.spinbox.value() == 3


def test_buying_nothing_does_nothing(game):
    name = planet_item(game)
    money = game.state.money
    dialog = Buy(game, name)
    dialog.acceptButtonClicked()
    assert game.state.money == money
    assert game.state.items.count() == 0


def test_buy_button_needs_a_selection(game, dialogs):
    game.planetItemBrowser.table.setCurrentCell(-1, -1)
    game.planetItemBrowser.buyButtonClicked()
    assert dialogs.messages("error") == ["Please select an item to buy first!"]
    assert dialogs.executed == []


def test_buy_button_opens_buy_dialog(game, dialogs):
    name = planet_item(game)
    select(game.planetItemBrowser, name)
    game.planetItemBrowser.buyButtonClicked()
    assert [type(d) for d in dialogs.executed] == [Buy]
    assert dialogs.executed[0].itemName == name


def test_buy_button_when_ship_is_full(game, dialogs):
    name = planet_item(game)
    give(game.state.items, "antimatter", game.state.capacity)
    select(game.planetItemBrowser, name)
    game.planetItemBrowser.buyButtonClicked()
    assert dialogs.titles("error") == ["Maximum capacity"]
    assert dialogs.executed == []


def test_buy_button_when_planet_has_none_left(game, dialogs):
    name = planet_item(game)
    game.state.current_planet.items.items[name].quantity = 0
    select(game.planetItemBrowser, name)
    game.planetItemBrowser.buyButtonClicked()
    assert dialogs.messages("error") == ["%s has no %s left to sell" % (game.state.current_planet.full_name, name)]


def test_sell(game):
    state = game.state
    name = planet_item(game)
    price = state.current_planet.items.items[name].value
    give(state.items, name, 50)
    money = state.money

    dialog = Sell(game, name)
    dialog.maxButtonClicked()
    assert dialog.spinbox.value() == 50
    dialog.spinbox.setValue(20)
    dialog.acceptButtonClicked()

    assert state.items.items[name].quantity == 30
    assert state.money == money + 20 * price
    assert game.audio.played == ["SellSound"]


def test_sell_all_sells_only_what_the_planet_trades(game, dialogs):
    state = game.state
    name = planet_item(game)
    price = state.current_planet.items.items[name].value
    not_traded = untraded_item(game)
    give(state.items, name, 10)
    give(state.items, not_traded, 5)
    money = state.money

    game.playerItemBrowser.sellAllButtonClicked()
    assert "(total gain: {:,})".format(10 * price) in dialogs.messages("question")[0]
    assert state.money == money + 10 * price
    assert list(state.items.items) == [not_traded]


def test_sell_all_when_planet_trades_none_of_it(game, dialogs):
    state = game.state
    not_traded = untraded_item(game)
    give(state.items, not_traded, 5)
    game.playerItemBrowser.sellAllButtonClicked()
    assert dialogs.titles("error") == ["Items cannot be sold"]
    assert state.items.count() == 5


@pytest.fixture
def sample_item(game):
    """
    An item on the ship that the current planet doesn't trade
    """
    name = untraded_item(game)
    give(game.state.items, name, 20)
    select(game.playerItemBrowser, name)
    return name


def test_free_sample_accepted(game, dialogs, sample_item, monkeypatch):
    monkeypatch.setattr(const, "ITEM_SAMPLE_SUCCESS_PERCENT", 100)
    game.playerItemBrowser.sellButtonClicked()

    planet = game.state.current_planet
    given = 20 - game.state.items.items[sample_item].quantity
    low, high = const.ITEM_SAMPLE_QUANTITY_RANGE
    assert low <= given < high
    assert "free sample of %d %s" % (given, sample_item) in dialogs.messages("question")[0]
    assert planet.items.items[sample_item].quantity == given
    assert dialogs.titles("info") == ["Good news!"]
    assert sample_item in column(game.planetItemBrowser.table, 0)


def test_free_sample_rejected(game, dialogs, sample_item, monkeypatch):
    monkeypatch.setattr(const, "ITEM_SAMPLE_SUCCESS_PERCENT", 0)
    game.playerItemBrowser.sellButtonClicked()
    assert sample_item not in game.state.current_planet.items.items
    assert game.state.items.items[sample_item].quantity < 20
    assert dialogs.titles("info") == ["Bad news!"]


def test_only_one_free_sample_per_day(game, dialogs, sample_item, monkeypatch):
    monkeypatch.setattr(const, "ITEM_SAMPLE_SUCCESS_PERCENT", 0)
    game.playerItemBrowser.sellButtonClicked()
    left = game.state.items.items[sample_item].quantity

    game.playerItemBrowser.sellButtonClicked()
    assert dialogs.titles("error") == ["Already sampled today"]
    assert game.state.items.items[sample_item].quantity == left


def test_free_sample_declined(game, dialogs, sample_item):
    dialogs.answers["Provide sample?"] = False
    game.playerItemBrowser.sellButtonClicked()
    assert game.state.items.items[sample_item].quantity == 20
    assert sample_item not in game.state.current_planet.items.items


@pytest.mark.parametrize("answer", [True, False])
def test_dump_ship_items(game, dialogs, answer):
    # Answering "No" used to close the dialog anyway
    give(game.state.items, "tin", 10)
    dialog = DumpPlayerItem(game, "tin")
    dialog.show()
    dialog.spinbox.setValue(4)
    dialogs.answers["Dump items?"] = answer
    dialog.acceptButtonClicked()

    assert game.state.items.items["tin"].quantity == (6 if answer else 10)
    assert dialog.isVisible() == (not answer)
    assert "Are you sure you want to dump 4 tin?" in dialogs.messages("question")[0]


def test_dump_all_ship_items(game, dialogs):
    give(game.state.items, "tin", 10)
    give(game.state.items, "gold", 10)
    game.updatePlayerItemsLabel()
    assert game.playerItemBrowserGroup.title() == "Items on your ship (20/%d)" % game.state.capacity
    game.playerItemBrowser.dumpAllButtonClicked()
    assert game.state.items.count() == 0
    assert game.playerItemBrowserGroup.title() == "Items on your ship (0/%d)" % game.state.capacity


def test_ship_buttons_with_no_items(game, dialogs):
    browser = game.playerItemBrowser
    for button in (browser.sellButtonClicked, browser.sellAllButtonClicked, browser.dumpButtonClicked,
                   browser.dumpAllButtonClicked, browser.warehouseButtonClicked):
        button()

    assert dialogs.titles("error") == ["No items"] * 5


def test_selection_survives_refresh(game):
    name = planet_item(game)
    browser = game.planetItemBrowser
    select(browser, name)
    browser.table.sortItems(2)
    browser.update()
    assert selectedItemName(browser.table) == name


@pytest.mark.parametrize("col", [1, 2, 3])
def test_number_columns_sort_by_value(game, col):
    give(game.state.current_planet.items, "antimatter", 1234567)
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.German, QtCore.QLocale.Germany))
    browser = game.planetItemBrowser
    browser.update()
    browser.table.sortItems(col)
    values = [browser.table.item(row, col).value for row in range(browser.table.rowCount())]
    assert values == sorted(values)


def test_enter_opens_price_history_for_selected_item(game, dialogs):
    name = planet_item(game)
    select(game.planetItemBrowser, name)
    QtTest.QTest.keyClick(game.planetItemBrowser, QtCore.Qt.Key_Return)
    assert [type(d) for d in dialogs.executed] == [PriceHistoryGraph]
    assert dialogs.executed[0].windowTitle() == "Price history for %s on %s" % (
        name, game.state.current_planet.full_name)


def test_enter_with_no_selection_does_nothing(game, dialogs):
    # Bug 4: this used to crash when no row was current
    game.planetItemBrowser.table.setCurrentCell(-1, -1)
    QtTest.QTest.keyClick(game.planetItemBrowser, QtCore.Qt.Key_Enter)
    assert dialogs.executed == []


class ItemNameTranslator(QtCore.QTranslator):
    """
    Translates item names only, so tables show names that differ from the item keys
    """
    def translate(self, context, source, disambiguation=None, n=-1):
        if context == "Items":
            return "XX-" + source

        return None


@pytest.fixture
def translated_item_names(qapp):
    translator = ItemNameTranslator()
    qapp.installTranslator(translator)
    yield
    qapp.removeTranslator(translator)


def test_tables_work_with_translated_item_names(game, dialogs, translated_item_names):
    # Tables used to look items up by the name shown, which breaks once item
    # names are translated
    name = planet_item(game)
    browser = game.planetItemBrowser
    select(browser, name)
    assert browser.table.item(browser.table.currentRow(), 0).text() == "XX-" + name

    browser.buyButtonClicked()
    QtTest.QTest.keyClick(browser, QtCore.Qt.Key_Return)
    assert [type(d) for d in dialogs.executed] == [Buy, PriceHistoryGraph]
    assert dialogs.executed[0].itemName == name

    give(game.state.items, name, 5)
    select(game.playerItemBrowser, name)
    game.playerItemBrowser.dumpButtonClicked()
    assert dialogs.executed[-1].itemName == name

    game.playerItemBrowser.update()
    assert selectedItemName(game.playerItemBrowser.table) == name
