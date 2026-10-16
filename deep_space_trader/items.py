import copy
import random

import numpy

from deep_space_trader import constants as const
from deep_space_trader.i18n import translate

from PyQt5.QtCore import QT_TRANSLATE_NOOP


def itemDisplayName(name):
    """
    Translated name of an item type, for showing to the player. Item type names
    themselves stay in English, since they are used as keys everywhere
    """
    return translate("Items", name)


class ItemType(object):
    def __init__(self, name, base_value):
        self.name = name
        self.base_value = base_value

    @property
    def display_name(self):
        return itemDisplayName(self.name)


common_item_types = [
    ItemType(QT_TRANSLATE_NOOP("Items", "tin"), const.PRICE_TIN),
    ItemType(QT_TRANSLATE_NOOP("Items", "steel"), const.PRICE_STEEL),
    ItemType(QT_TRANSLATE_NOOP("Items", "copper"), const.PRICE_COPPER),
    ItemType(QT_TRANSLATE_NOOP("Items", "silver"), const.PRICE_SILVER),
]

medium_rare_item_types = [
    ItemType(QT_TRANSLATE_NOOP("Items", "gold"), const.PRICE_GOLD),
    ItemType(QT_TRANSLATE_NOOP("Items", "silicon"), const.PRICE_SILICON),
    ItemType(QT_TRANSLATE_NOOP("Items", "uranium"), const.PRICE_URANIUM),
    ItemType(QT_TRANSLATE_NOOP("Items", "diamond"), const.PRICE_DIAMOND),
    ItemType(QT_TRANSLATE_NOOP("Items", "tritium"), const.PRICE_TRITIUM),
    ItemType(QT_TRANSLATE_NOOP("Items", "platinum"), const.PRICE_PLATINUM),
    ItemType(QT_TRANSLATE_NOOP("Items", "plutonium"), const.PRICE_PLUTONIUM)
]

rare_item_types = [
    ItemType(QT_TRANSLATE_NOOP("Items", "jade stone"), const.PRICE_JADESTONE),
    ItemType(QT_TRANSLATE_NOOP("Items", "antimatter"), const.PRICE_ANTIMATTER)
]

# Illegal goods. Only black markets trade them (see State.expand_planets), and
# they can be seized by customs patrols when carried on the ship
contraband_item_types = [
    ItemType(QT_TRANSLATE_NOOP("Items", "untaxed tobacco"), const.PRICE_TOBACCO),
    ItemType(QT_TRANSLATE_NOOP("Items", "bootleg liquor"), const.PRICE_LIQUOR),
    ItemType(QT_TRANSLATE_NOOP("Items", "combat stimulants"), const.PRICE_STIMULANTS),
    ItemType(QT_TRANSLATE_NOOP("Items", "counterfeit credit chips"), const.PRICE_CREDIT_CHIPS),
    ItemType(QT_TRANSLATE_NOOP("Items", "military ammunition"), const.PRICE_AMMUNITION)
]

contraband_item_names = frozenset(t.name for t in contraband_item_types)


def isContraband(itemname):
    return itemname in contraband_item_names


class Scarcity:
    EXTREMELY_SCARCE = 0
    VERY_SCARCE = 1
    MODERATELY_SCARCE = 2
    PLENTIFUL = 3
    MODERATELY_PLENTIFUL = 4
    VERY_PLENTIFUL = 5
    EXTREMELY_PLENTIFUL = 6

    @classmethod
    def score(cls, quantity):
        quantity = int(quantity)
        if quantity < 100:
            return cls.EXTREMELY_SCARCE
        elif quantity < 1000:
            return cls.VERY_SCARCE
        elif quantity < 10000:
            return cls.MODERATELY_SCARCE
        elif quantity < 100000:
            return cls.PLENTIFUL
        elif quantity < 1000000:
            return cls.MODERATELY_PLENTIFUL
        elif quantity < 10000000:
            return cls.VERY_PLENTIFUL

        return cls.EXTREMELY_PLENTIFUL


scarcity_price_offsets = {
    Scarcity.EXTREMELY_SCARCE: 0.5,
    Scarcity.VERY_SCARCE: 0.4,
    Scarcity.MODERATELY_SCARCE: 0.3,
    Scarcity.PLENTIFUL: 0.2,
    Scarcity.MODERATELY_PLENTIFUL: 0.15,
    Scarcity.VERY_PLENTIFUL: 0.1,
    Scarcity.EXTREMELY_PLENTIFUL: 0.0
}

scarcity_price_init_factors = {
    Scarcity.EXTREMELY_SCARCE: 1.0,
    Scarcity.VERY_SCARCE: 0.75,
    Scarcity.MODERATELY_SCARCE: 0.5,
    Scarcity.PLENTIFUL: 0.0,
    Scarcity.MODERATELY_PLENTIFUL: -0.1,
    Scarcity.VERY_PLENTIFUL: -0.25,
    Scarcity.EXTREMELY_PLENTIFUL: -0.5
}

def quantityRange(itemtype):
    """
    (smallest, largest) amount of an item type that a planet starts with.
    (Item types are compared by name, since items moved from one collection to
    another are copies, with copies of their item types)
    """
    name = itemtype.name
    if name in contraband_item_names:
        return const.BLACK_MARKET_QUANTITY_RANGE
    if any(name == t.name for t in rare_item_types):
        return const.RARE_QUANTITY_RANGE
    if any(name == t.name for t in medium_rare_item_types):
        return const.MEDIUM_RARE_QUANTITY_RANGE

    return const.COMMON_QUANTITY_RANGE


def randomQuantity(itemtype, quantity_multiplier=1.0):
    """
    A random amount of an item type for a planet to start with
    """
    low, high = quantityRange(itemtype)
    return random.randrange(low, high + 1) * quantity_multiplier


def restockedQuantity(quantity, target, days, normal):
    """
    Stock after 'days' days of drifting towards 'target' (see Items.restock).
    'normal' is a random number from a normal distribution (mean 0, standard
    deviation 1). Works on numbers, or on numpy arrays of them (one per item).

    Each day, the stock moves part of the way to the target (the same part
    every day, so the further away it is, the bigger the change), plus some
    noise. This is the exact result of doing that 'days' times, in one go: the
    gap shrinks by r ** days, and the noise of all the days adds up to one
    random amount, so that catching up 10 days at once behaves like 10 single days
    """
    r = 0.5 ** (1.0 / const.STOCK_RECOVERY_HALF_LIFE_DAYS)
    left = r ** days
    noise = const.STOCK_NOISE_FRACTION * target * numpy.sqrt(1.0 - left * left) * normal
    return numpy.maximum(0, numpy.round(target + (quantity - target) * left + noise))


class Items(object):
    def __init__(self, itemtype, quantity, value=None):
        self.type = itemtype
        self._scarcity = 0.0
        self._quantity = quantity

        # The amount this planet's stock drifts back towards (see restock)
        self.target_quantity = quantity
        self._daily_variance = random.uniform(0.0, 1.5)

        if value is None:
            self._value = float(itemtype.base_value)
        else:
            self._value = float(value)

        init_factor = scarcity_price_init_factors[Scarcity.score(quantity)]
        self._value += (self._value * init_factor)
        variance = 1.0

        # Initial slope value
        self.value_slope = random.uniform(-variance, variance)
        self.value_history = [self.value]

    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self, new):
        slope_add = scarcity_price_offsets[Scarcity.score(new)]

        if new > self._quantity:
            # Becoming more plentiful
            self.value_slope -= random.uniform(0.0, slope_add)
        elif new < self._quantity:
            # Becoming more scarce
            self.value_slope += random.uniform(0.0, slope_add)

        self._quantity = new

    @property
    def value(self):
        return int(self._value)

    @value.setter
    def value(self, new):
        self._value = float(new)

    @property
    def total_value(self):
        return self.value * self.quantity

    def update_value(self):
        # Random value within range for daily variance
        change = random.uniform(-self._daily_variance, self._daily_variance)

        # Update current slope
        self.value_slope += change

        if (self._value + self.value_slope) > 1.0:
            # Update value with current slope
            self._value += self.value_slope

        # Update value history
        self.value_history.append(self.value)

    def restock(self, days):
        """
        Let 'days' days pass for this item on a planet's market: other traders
        buy and sell, so the stock drifts back towards its starting amount (see
        restockedQuantity). Prices aren't affected
        """
        if days <= 0:
            return

        # (Not through the quantity setter, which nudges the price trend)
        self._quantity = int(restockedQuantity(self._quantity, self.target_quantity, days, random.gauss(0.0, 1.0)))

    @classmethod
    def random(cls, value_multiplier=1.0, quantity_multiplier=1.0):
        prob = random.randrange(0, 100)
        choices = None

        if prob >= 95:
            # 5% chance of a rare item
            choices = rare_item_types
        elif prob >= 75:
            # 25% chance of a rare or medium rare item
            choices = medium_rare_item_types
        else:
            # otherwise, a common item
            choices = common_item_types

        itemtype = random.choice(choices)
        quantity = randomQuantity(itemtype, quantity_multiplier)

        value = random.randrange(int(itemtype.base_value / 2), int(itemtype.base_value * 2))
        value *= value_multiplier

        return Items(itemtype, quantity, value)


class ItemCollection(object):
    def __init__(self, items=[]):
        self.items = {}

        for item in items:
            if item.type.name not in self.items:
                self.items[item.type.name] = item
            else:
                self.items[item.type.name].quantity += item.quantity
                self.items[item.type.name].target_quantity += item.quantity

    @property
    def total_value(self):
        ret = 0
        for n in self.items:
            ret += self.items[n].total_value

        return ret

    def iter_items(self):
        for itemname in self.items:
            yield self.items[itemname]

    def remove_items(self, itemname, quantity=1, delete_empty=True):
        if itemname not in self.items:
            return

        num = min(quantity, self.items[itemname].quantity)
        self.items[itemname].quantity -= num

        if (self.items[itemname].quantity == 0) and delete_empty:
            del self.items[itemname]

    def remove_all_items(self):
        self.items = {}

    def add_items(self, itemname, other, quantity=1, delete_empty=True):
        if itemname not in other.items:
            return

        if itemname not in self.items:
            self.items[itemname] = copy.deepcopy(other.items[itemname])
            self.items[itemname].quantity = 0

        num = min(quantity, other.items[itemname].quantity)
        self.items[itemname].quantity += num
        other.items[itemname].quantity -= num

        if (other.items[itemname].quantity == 0) and delete_empty:
            del other.items[itemname]

    def add_all_items(self, other, delete_empty=True):
        for name in list(other.items.keys()):
            if other.items[name].quantity > 0:
                self.add_items(name, other, other.items[name].quantity, delete_empty)

    def count(self):
        ret = 0
        for name in self.items:
            ret += self.items[name].quantity

        return ret

    @classmethod
    def random(cls, num=None, value_multiplier=1.0, quantity_multiplier=1.0):
        if num is None:
            num = random.randrange(2, 25)

        items = [Items.random(value_multiplier, quantity_multiplier) for _ in range(num)]
        return ItemCollection(items)
