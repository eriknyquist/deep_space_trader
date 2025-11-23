import copy
import random

from deep_space_trader import constants as const


class ItemType(object):
    def __init__(self, name, base_value):
        self.name = name
        self.base_value = base_value


common_item_types = [
    ItemType("tin", const.PRICE_TIN),
    ItemType("steel", const.PRICE_STEEL),
    ItemType("copper", const.PRICE_COPPER),
    ItemType("silver", const.PRICE_SILVER),
]

medium_rare_item_types = [
    ItemType("gold", const.PRICE_GOLD),
    ItemType("silicon", const.PRICE_SILICON),
    ItemType("uranium", const.PRICE_URANIUM),
    ItemType("diamond", const.PRICE_DIAMOND),
    ItemType("tritium", const.PRICE_TRITIUM),
    ItemType("platinum", const.PRICE_PLATINUM),
    ItemType("plutonium", const.PRICE_PLUTONIUM)
]

rare_item_types = [
    ItemType("jade stone", const.PRICE_JADESTONE),
    ItemType("antimatter", const.PRICE_ANTIMATTER)
]


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

class Items(object):
    def __init__(self, itemtype, quantity, value=None):
        self.type = itemtype
        self._scarcity = 0.0
        self._quantity = quantity
        self._daily_variance = random.uniform(0.0, 1.5)

        if value is None:
            self_value = float(itemtype.base_value)
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
        self._value = float(self._value)

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

    @classmethod
    def random(cls, value_multiplier=1.0, quantity_multiplier=1.0):
        prob = random.randrange(0, 100)
        choices = None
        quantity_range = None

        if prob >= 95:
            # 5% chance of a rare item
            choices = rare_item_types
            quantity_range = const.RARE_QUANTITY_RANGE
        elif prob >= 75:
            # 25% chance of a rare or medium rare item
            choices = medium_rare_item_types
            quantity_range = const.MEDIUM_RARE_QUANTITY_RANGE
        else:
            # otherwise, a common item
            choices = common_item_types
            quantity_range = const.COMMON_QUANTITY_RANGE

        itemtype = random.choice(choices)
        quantity = random.randrange(quantity_range[0], quantity_range[1] + 1)
        quantity *= quantity_multiplier

        value = random.randrange(int(itemtype.base_value / 2), int(itemtype.base_value * 2))
        value *= value_multiplier

        return Items(itemtype, quantity, value)


class ItemCollection(object):
    def __init__(self, items=[]):
        self.items = {}

        for item in items:
            if item.type.name not in self.items:
                self.items[item.type.name] = item

            self.items[item.type.name].quantity += item.quantity

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
