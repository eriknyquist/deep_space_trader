"""
Helpers shared by the tests (fixtures are in conftest.py)
"""
from deep_space_trader import utils
from deep_space_trader.items import (
    ItemCollection, Items, common_item_types, medium_rare_item_types, rare_item_types
)

ALL_ITEM_TYPES = common_item_types + medium_rare_item_types + rare_item_types
ALL_ITEM_NAMES = [t.name for t in ALL_ITEM_TYPES]


class FakeAudio(object):
    """
    Silent stand-in for sounds.AudioPlayer. Sound names are attributes, as on
    the real player (audio.TravelSound == "TravelSound"), and played sounds are
    recorded in 'played'
    """
    def __init__(self):
        self.played = []
        self.enabled = True

    def __getattr__(self, name):
        if name.endswith("Sound"):
            return name

        raise AttributeError(name)

    def play(self, sound):
        if self.enabled:
            self.played.append(sound)

    def setEnabled(self, enabled):
        self.enabled = enabled


def stock():
    """
    A collection with a large quantity of every item type, to take items from
    """
    return ItemCollection([Items(t, 10 ** 7, 10) for t in ALL_ITEM_TYPES])


def give(collection, itemname, quantity):
    """
    Add 'quantity' of an item to a collection (e.g. the ship or the warehouse)
    """
    collection.add_items(itemname, stock(), quantity, delete_empty=False)


def row_of(table, key):
    """
    Row whose first cell stores 'key' (a Planet, or an item type name)
    """
    for row in range(table.rowCount()):
        if utils.rowKey(table, row) == key:
            return row

    raise AssertionError("%r is not in the table" % (key,))


def column(table, col):
    return [table.item(row, col).text() for row in range(table.rowCount())]
