import random

import pytest

from deep_space_trader import constants as const
from deep_space_trader import store


def store_item(cls):
    return next(item for item in store.store_items if isinstance(item, cls))


@pytest.fixture
def shop(game):
    game.state.max_store_purchases_per_day = 1000
    return store.Store(game)


def test_store_lists_every_item(shop):
    names = [shop.table.item(row, 0).text() for row in range(shop.table.rowCount())]
    assert names == ["Increase ship capacity", "Scout expedition", "Planet destruction kit",
                     "Buy scout fleet", "Buy battle fleet", "Increase max. warehouse trips per day",
                     "Trading console"]


def test_capacity_increase_doubles_each_time(game, shop):
    item = store_item(store.CapacityIncrease)
    state = game.state
    money = state.money

    shop.buyItem(item)
    assert state.capacity == const.INITIAL_ITEM_CAPACITY + const.CAPACITY_INCREASE
    assert state.money == money - const.CAPACITY_INCREASE_COST
    assert state.store_purchases == 1
    assert item.price == const.CAPACITY_INCREASE_COST * 2

    shop.buyItem(item)
    assert state.capacity == const.INITIAL_ITEM_CAPACITY + 3 * const.CAPACITY_INCREASE
    assert game.playerItemBrowserGroup.title() == "Items on your ship (0/%d)" % state.capacity


def test_declining_a_purchase_changes_nothing(game, shop, dialogs):
    dialogs.answers["Are you sure?"] = False
    shop.buyItem(store_item(store.CapacityIncrease))
    assert game.state.capacity == const.INITIAL_ITEM_CAPACITY
    assert game.state.store_purchases == 0


def test_not_enough_money(game, shop, dialogs):
    game.state.money = const.CAPACITY_INCREASE_COST - 1
    shop.buyItem(store_item(store.CapacityIncrease))
    assert dialogs.messages("error") == ["You don't have enough money to buy 'Increase ship capacity'"]
    assert game.state.capacity == const.INITIAL_ITEM_CAPACITY
    assert game.state.money == const.CAPACITY_INCREASE_COST - 1


def test_daily_purchase_limit(game, shop, dialogs):
    game.state.max_store_purchases_per_day = 4
    game.state.store_purchases = 4
    shop.buyItem(store_item(store.CapacityIncrease))
    assert dialogs.messages("error") == ["You can only make 4 store purchases per day. Come back tomorrow."]
    assert game.state.capacity == const.INITIAL_ITEM_CAPACITY


def test_store_button_refuses_when_limit_reached(game, dialogs):
    game.state.store_purchases = game.state.max_store_purchases_per_day
    game.buttonBar.storeButtonClicked()
    assert dialogs.titles("error") == ["Sorry!"]
    assert dialogs.executed == []


def test_store_button_opens_store(game, dialogs):
    game.buttonBar.storeButtonClicked()
    assert [type(d) for d in dialogs.executed] == [store.Store]


def test_scout_expedition_needs_a_scout_fleet(game, shop, dialogs):
    planets = len(game.state.planets)
    shop.buyItem(store_item(store.PlanetExploration))
    assert dialogs.titles("error") == ["Sorry!"]
    assert len(game.state.planets) == planets
    assert game.state.store_purchases == 0


def test_scout_fleet_purchase_and_upgrades(game, shop):
    item = store_item(store.ScoutFleetUpgrade)
    state = game.state
    daily_cost = state.daily_cost

    shop.buyItem(item)
    assert state.scout_level == 1
    assert state.planet_discovery_range == const.PLANET_DISCOVERY_RANGE
    assert state.daily_cost == daily_cost + const.DAILY_SCOUT_FLEET_COST_PER_LEVEL
    assert item.name == "Upgrade scout fleet"

    shop.buyItem(item)
    assert state.scout_level == 2
    low, high = const.PLANET_DISCOVERY_RANGE
    assert state.planet_discovery_range == (low * 2, high * 2)


def test_scout_fleet_maximum_level(game, shop, dialogs):
    item = store_item(store.ScoutFleetUpgrade)
    game.state.money = 10 ** 15
    for _ in range(const.MAX_SCOUT_LEVEL):
        shop.buyItem(item)

    assert game.state.scout_level == const.MAX_SCOUT_LEVEL
    assert item.price is None
    assert item.description == "You cannot buy this item anymore."

    purchases = game.state.store_purchases
    shop.buyItem(item)
    assert game.state.store_purchases == purchases
    assert dialogs.messages("error")[-1] == "You cannot buy this item anymore"


@pytest.mark.parametrize("level", [1, 2])
def test_scout_expedition_covers_the_whole_range(game, level):
    # Bug 12: the top of the range was never reached
    state = game.state
    state.scout_level = level
    low, high = (x * 2 ** (level - 1) for x in const.PLANET_DISCOVERY_RANGE)
    state.planet_discovery_range = (low, high)
    item = store_item(store.PlanetExploration)

    random.seed(30)
    found = set()
    before = len(state.planets)
    for _ in range(100):
        assert item.use()
        found.add(len(state.planets) - before)
        # Keep the planet table small, so this stays fast
        del state.planets[before:]

    assert min(found) == low
    assert max(found) == high


def test_scout_expedition_stops_at_the_planet_limit(game, shop, dialogs, monkeypatch):
    state = game.state
    state.scout_level = 1
    monkeypatch.setattr(const, "MAX_PLANETS_ALLOWED", len(state.planets) + 2)
    item = store_item(store.PlanetExploration)

    shop.buyItem(item)
    assert len(state.planets) == const.MAX_PLANETS_ALLOWED
    assert "2 new planets" in dialogs.titles("info")[-1]

    shop.buyItem(item)
    assert len(state.planets) == const.MAX_PLANETS_ALLOWED
    assert dialogs.titles("error") == ["Sorry!"]


def test_scout_expedition_shows_new_planets(game, shop):
    game.state.scout_level = 1
    shop.buyItem(store_item(store.PlanetExploration))
    assert game.locationBrowser.table.rowCount() == len(game.state.planets)
    assert game.locationBrowserGroup.title() == "Planets (%d)" % len(game.state.planets)


def test_battle_fleet_purchase_and_upgrades(game, shop, dialogs):
    item = store_item(store.BattleFleetUpgrade)
    state = game.state
    state.money = 10 ** 15
    daily_cost = state.daily_cost

    shop.buyItem(item)
    assert state.battle_level == 1
    assert item.name == "Upgrade battle fleet"
    assert dialogs.messages("info")[-1] == "Battle fleet successfully purchased."

    for _ in range(const.MAX_BATTLE_LEVEL - 1):
        shop.buyItem(item)

    assert state.battle_level == const.MAX_BATTLE_LEVEL
    assert state.daily_cost == daily_cost + const.MAX_BATTLE_LEVEL * const.DAILY_BATTLE_FLEET_COST_PER_LEVEL
    assert dialogs.messages("info")[-1] == "Battle fleet successfully upgraded."
    assert item.price is None


def test_warehouse_trips_increase(game, shop):
    shop.buyItem(store_item(store.WarehouseSpeedIncrease))
    assert game.state.warehouse_trips_per_day == const.WAREHOUSE_TRIPS_PER_DAY + 2


def test_trading_console(game, shop):
    item = store_item(store.TradingConsole)
    assert not game.locationBrowser.pricesButton.isEnabled()

    shop.buyItem(item)
    assert game.state.have_trading_console
    assert game.locationBrowser.pricesButton.isEnabled()
    assert item.price is None
    assert shop.table.item(6, 2).text() == "N/A"


def test_cancelled_planet_destruction_is_not_a_purchase(game, shop, dialogs):
    shop.buyItem(store_item(store.PlanetDestruction))
    assert len(dialogs.executed) == 1
    assert game.state.store_purchases == 0
    assert len(game.state.planets) == const.INITIAL_PLANET_COUNT
