import pytest

from deep_space_trader.transaction_dialogs import PlayerToWarehouse, WarehouseToPlayer, DumpWarehouseItem

from helpers import give, row_of


def select(browser, itemname):
    browser.update()
    browser.table.setCurrentCell(row_of(browser.table, itemname), 0)


def test_move_to_warehouse_uses_a_trip(game):
    state = game.state
    give(state.items, "tin", 30)

    dialog = PlayerToWarehouse(game, "tin")
    dialog.spinbox.setValue(20)
    dialog.acceptButtonClicked()

    assert state.items.items["tin"].quantity == 10
    assert state.warehouse.items["tin"].quantity == 20
    assert state.warehouse_trips == 1
    assert game.infoBar.warehouseTripsLabel.text() == "1/2"


def test_retrieve_is_limited_by_free_space(game):
    state = game.state
    give(state.warehouse, "tin", 500)
    give(state.items, "gold", state.capacity - 15)

    dialog = WarehouseToPlayer(game, "tin")
    dialog.maxButtonClicked()
    assert dialog.spinbox.value() == 15
    dialog.acceptButtonClicked()

    assert state.items.count() == state.capacity
    assert state.warehouse.items["tin"].quantity == 485
    assert state.warehouse_trips == 1


def test_no_trips_left(game, dialogs):
    state = game.state
    give(state.items, "tin", 10)
    give(state.warehouse, "gold", 10)
    select(game.playerItemBrowser, "tin")
    select(game.warehouseItemBrowser, "gold")
    state.warehouse_trips = state.warehouse_trips_per_day

    game.playerItemBrowser.warehouseButtonClicked()
    game.warehouseItemBrowser.removeButtonClicked()
    game.warehouseItemBrowser.removeAllButtonClicked()
    assert dialogs.titles("error") == ["Warehouse"] * 3
    assert dialogs.executed == []
    assert state.warehouse.items["gold"].quantity == 10


def test_trips_reset_each_day(game):
    game.state.warehouse_trips = 2
    game.advanceDay()
    assert game.state.warehouse_trips == 0


def test_warehouse_buttons_open_dialogs(game, dialogs):
    give(game.state.items, "tin", 10)
    give(game.state.warehouse, "gold", 10)
    select(game.playerItemBrowser, "tin")
    select(game.warehouseItemBrowser, "gold")

    game.playerItemBrowser.warehouseButtonClicked()
    game.warehouseItemBrowser.removeButtonClicked()
    game.warehouseItemBrowser.dumpButtonClicked()
    assert [type(d) for d in dialogs.executed] == [PlayerToWarehouse, WarehouseToPlayer, DumpWarehouseItem]


def test_retrieve_all(game, dialogs):
    state = game.state
    give(state.warehouse, "tin", 30)
    give(state.warehouse, "gold", 20)

    game.warehouseItemBrowser.removeAllButtonClicked()
    assert dialogs.messages("question") == ["Are you sure you want to retrieve all items?"]
    assert state.items.items["tin"].quantity == 30
    assert state.items.items["gold"].quantity == 20
    assert state.warehouse.count() == 0
    assert state.warehouse_trips == 1


def test_retrieve_all_when_only_some_fit(game, dialogs):
    state = game.state
    give(state.warehouse, "tin", 300)
    give(state.items, "gold", state.capacity - 25)

    game.warehouseItemBrowser.removeAllButtonClicked()
    assert "the maximum number of items that can be retrieved is 25" in dialogs.messages("question")[0]
    assert state.items.count() == state.capacity
    assert state.warehouse.items["tin"].quantity == 275
    assert state.warehouse_trips == 1


def test_retrieve_all_when_ship_is_full(game, dialogs):
    # Used to offer to retrieve 0 items, and use up a trip
    state = game.state
    give(state.warehouse, "tin", 30)
    give(state.items, "gold", state.capacity)

    game.warehouseItemBrowser.removeAllButtonClicked()
    assert dialogs.titles("error") == ["Maximum capacity"]
    assert dialogs.messages("question") == []
    assert state.warehouse_trips == 0
    assert state.warehouse.items["tin"].quantity == 30


def test_retrieve_all_can_be_declined(game, dialogs):
    give(game.state.warehouse, "tin", 30)
    dialogs.answers["Are you sure?"] = False
    game.warehouseItemBrowser.removeAllButtonClicked()
    assert game.state.warehouse.items["tin"].quantity == 30
    assert game.state.warehouse_trips == 0


def test_empty_warehouse(game, dialogs):
    browser = game.warehouseItemBrowser
    browser.removeButtonClicked()
    browser.removeAllButtonClicked()
    browser.dumpButtonClicked()
    browser.dumpAllButtonClicked()
    assert dialogs.titles("error") == ["Warehouse", "Warehouse", "Warehouse", "No items"]


@pytest.mark.parametrize("answer", [True, False])
def test_dump_warehouse_items(game, dialogs, answer):
    give(game.state.warehouse, "gold", 10)
    dialog = DumpWarehouseItem(game, "gold")
    dialog.show()
    dialog.spinbox.setValue(3)
    dialogs.answers["Dump items?"] = answer
    dialog.acceptButtonClicked()

    assert game.state.warehouse.items["gold"].quantity == (7 if answer else 10)
    assert dialog.isVisible() == (not answer)


def test_dump_all_warehouse_items(game, dialogs):
    give(game.state.warehouse, "gold", 10)
    give(game.state.warehouse, "tin", 10)
    game.warehouseItemBrowser.dumpAllButtonClicked()
    assert game.state.warehouse.count() == 0
    assert game.warehouseItemBrowser.table.rowCount() == 0
    assert game.audio.played == ["DumpSound"]


# ----- The warehouse is on the home planet -----

@pytest.fixture
def away_from_home(game):
    state = game.state
    state.change_current_planet(next(p for p in state.planets if p is not state.home_planet))
    return state.current_planet


def test_warehouse_moves_only_at_home(game, dialogs, away_from_home):
    state = game.state
    give(state.items, "tin", 10)
    give(state.warehouse, "gold", 10)
    select(game.playerItemBrowser, "tin")
    select(game.warehouseItemBrowser, "gold")

    game.playerItemBrowser.warehouseButtonClicked()
    game.warehouseItemBrowser.removeButtonClicked()
    game.warehouseItemBrowser.removeAllButtonClicked()
    game.warehouseItemBrowser.onDoubleClick()

    message = "Your warehouse is on %s. Travel there to use it." % state.home_planet.full_name
    assert dialogs.messages("error") == [message] * 4
    assert dialogs.executed == []
    assert state.warehouse_trips == 0
    assert state.warehouse.items["gold"].quantity == 10
    assert state.items.items["tin"].quantity == 10


def test_warehouse_dumping_works_away_from_home(game, dialogs, away_from_home):
    give(game.state.warehouse, "gold", 10)
    select(game.warehouseItemBrowser, "gold")
    game.warehouseItemBrowser.dumpButtonClicked()
    assert [type(d) for d in dialogs.executed] == [DumpWarehouseItem]

    game.warehouseItemBrowser.dumpAllButtonClicked()
    assert game.state.warehouse.count() == 0


def test_warehouse_title_names_home_planet(game):
    title = game.warehouseItemsBrowserGroup.title
    assert title() == "Items in warehouse (on %s)" % game.state.home_planet.full_name

    game.reset()
    assert title() == "Items in warehouse (on %s)" % game.state.home_planet.full_name
