import random

import pytest

from deep_space_trader import constants as const
from deep_space_trader.items import (
    Items, ItemCollection, ItemType, itemDisplayName, common_item_types, medium_rare_item_types,
    rare_item_types
)

from helpers import ALL_ITEM_NAMES, give

TIN = common_item_types[0]
GOLD = medium_rare_item_types[0]


def test_item_names_are_unique():
    assert len(ALL_ITEM_NAMES) == len(set(ALL_ITEM_NAMES)) == 13


def test_display_name_is_the_name_when_untranslated():
    assert itemDisplayName("jade stone") == "jade stone"
    assert TIN.display_name == "tin"


def test_items_without_value_use_base_value():
    # Bug 8: a typo (self_value) made this raise AttributeError
    items = Items(TIN, 50000)
    assert items.value == TIN.base_value


@pytest.mark.parametrize("quantity, factor", [
    (50, 1.0),           # extremely scarce: price doubles
    (50000, 0.0),        # plentiful: no change
    (50000000, -0.5),    # extremely plentiful: price halves
])
def test_initial_price_depends_on_scarcity(quantity, factor):
    items = Items(GOLD, quantity, 100)
    assert items.value == int(100 + 100 * factor)


def test_total_value():
    items = Items(GOLD, 50000, 30)
    assert items.total_value == items.value * 50000


def test_collection_combines_stacks_of_the_same_type():
    # Bug 9: the first stack of each type used to be counted twice
    collection = ItemCollection([Items(TIN, 1000, 10), Items(TIN, 500, 10), Items(GOLD, 250, 10)])
    assert collection.items["tin"].quantity == 1500
    assert collection.items["gold"].quantity == 250
    assert collection.count() == 1750


def test_random_collection_totals_match_their_stacks():
    random.seed(5)
    for _ in range(50):
        stacks = [Items.random() for _ in range(10)]
        expected = {}
        for s in stacks:
            expected[s.type.name] = expected.get(s.type.name, 0) + s.quantity

        collection = ItemCollection(stacks)
        assert {n: i.quantity for n, i in collection.items.items()} == expected


def test_random_items_quantities_are_in_range():
    random.seed(6)
    ranges = {}
    for types, rng in ((common_item_types, const.COMMON_QUANTITY_RANGE),
                       (medium_rare_item_types, const.MEDIUM_RARE_QUANTITY_RANGE),
                       (rare_item_types, const.RARE_QUANTITY_RANGE)):
        for t in types:
            ranges[t.name] = rng

    for _ in range(500):
        items = Items.random()
        low, high = ranges[items.type.name]
        assert low <= items.quantity <= high


def test_add_items_moves_items_between_collections():
    source = ItemCollection([Items(TIN, 100, 10)])
    target = ItemCollection()

    target.add_items("tin", source, 30)
    assert target.items["tin"].quantity == 30
    assert source.items["tin"].quantity == 70


def test_add_items_moves_at_most_what_is_there():
    source = ItemCollection([Items(TIN, 100, 10)])
    target = ItemCollection()

    target.add_items("tin", source, 1000)
    assert target.items["tin"].quantity == 100
    assert "tin" not in source.items


def test_add_items_can_keep_empty_stacks():
    source = ItemCollection([Items(TIN, 100, 10)])
    target = ItemCollection()

    target.add_items("tin", source, 100, delete_empty=False)
    assert source.items["tin"].quantity == 0


def test_add_items_of_missing_type_does_nothing():
    source = ItemCollection()
    target = ItemCollection()
    target.add_items("tin", source, 10)
    assert target.count() == 0


def test_add_items_keeps_its_own_copy():
    source = ItemCollection([Items(TIN, 100, 10)])
    target = ItemCollection()
    target.add_items("tin", source, 10)
    assert target.items["tin"] is not source.items["tin"]


def test_remove_items():
    collection = ItemCollection([Items(TIN, 100, 10)])
    collection.remove_items("tin", 40)
    assert collection.items["tin"].quantity == 60

    collection.remove_items("tin", 1000)
    assert "tin" not in collection.items


def test_add_all_and_remove_all_items():
    source = ItemCollection([Items(TIN, 100, 10), Items(GOLD, 5, 10)])
    target = ItemCollection()
    give(target, "tin", 1)

    target.add_all_items(source)
    assert target.items["tin"].quantity == 101
    assert target.items["gold"].quantity == 5
    assert source.count() == 0

    target.remove_all_items()
    assert target.count() == 0


def test_update_value_records_history_and_stays_positive():
    random.seed(7)
    items = Items(ItemType("cheap", 2), 10, 2)
    for _ in range(500):
        items.update_value()

    assert len(items.value_history) == 501
    assert all(v >= 1 for v in items.value_history)
