import copy
import time
import random

from deep_space_trader.items import ItemCollection


def random_planet_number():
    return random.randrange(2, 399)

def random_planet_letter():
    return chr(random.randrange(97, 108))


class Planet(object):
    parts = [
        [
            'ho', 'ce', 'cu', 'he', 'hu', 'sa', 'cy', 'an', 'ir', 'kle', 'ke',
            'ka', 'la', 'ny', 'ky', 'dy', 'bar', 'blar', 'ger', 'yur', 'her',
            'zor', 'for', 'nor', 'wor', 'gor', 'noth', 'roth', 'moth', 'zoth',
            'loth', 'nith', 'lith', 'sith', 'dith', 'ith', 'oth', 'orb', 'urb',
            'erb', 'zorb', 'zor', 'zer', 'zerb', 'zera', 'ter', 'porb', 'por',
            'per', 'perb', 'pera', 'er', 'sta', 'morb', 'kur', 'kurb', 'lerb',
            'gra', 'bra', 'zir', 'dir', 'tir', 'sir', 'mir', 'nir', 'pir', 'lir',
            'bir'
        ],
        [
            'ta', 'te', 'ti', 'to', 'tu', 'ba', 'be', 'bi', 'bo', 'tis', 'ris',
            'beur', 'bu', 'po', 'cu', 'lur', 'mur', 'tu', 'da', 'de', 'di', 'do',
            'du', 'lor', 'der', 'ser', 'per', 'fu', 'fer', 'ler', 'zer', 'wi',
            'bre', 'dre', 'pre', 'tre', 're', 'fe', 'ge', 'ga', 'gu', 'du', 'mu',
            'nu', 'ru', 'mi', 'ni', 'su'
        ],
        [
            'res', 'lia', 'gese', 'naise', 'bler', 'pler', 'teres', 'tere',
            'pules', 'ner', 'yer', 'prer', 'padia', 'dium', 'dum', 'rem', 'tem',
            'tis', 'ratis', 'cus', 'rus', 'tus', 'rus', 'muth', 'yuth', 'reth',
            'doth', 'rath', 'bath', 'tath', 'path', 'adia', 'radia', 'anus',
            'nus', 'ban', 'tan', 'lan', 'dan', 'man', 'nan', 'xan', 'zan', 'pan',
            'ius', 'rious', 'tius', 'bius', 'sius', 'ise', 'use'
        ],
    ]

    @classmethod
    def num_possible_planets(cls):
        """
        Calculates the number of possible unique planet names based on the number
        of planet name parts we are working with
        """
        return ((len(cls.parts[0]) * len(cls.parts[1]) * len(cls.parts[2]) +
                (len(cls.parts[0]) * len(cls.parts[2]))))

    @classmethod
    def _random_planet(cls, long_name_prob=35, number_suffix_prob=35, letter_suffix_prob=35):
        if random.randrange(0, 100) < long_name_prob:
            # 3-part name
            indices = [0, 1, 2]
        else:
            # 2-part name
            indices = [0, 2]

        name = ""
        number = None
        letter = None

        for i in range(len(indices)):
            name += random.choice(cls.parts[indices[i]])

        if random.randrange(0, 100) < number_suffix_prob:
            number = random_planet_number()

            if random.randrange(0, 100) < letter_suffix_prob:
                letter = random_planet_letter()

        return Planet(name, number, letter)

    @classmethod
    def random(cls, num=1):
        max_group_size = 4
        last_planet_with_letter = None
        group_size = None
        ret = []

        for i in range(num):
            if last_planet_with_letter is not None:
                if group_size < max_group_size:
                    new = last_planet_with_letter.neighbour()
                    ret.append(new)
                    last_planet_with_letter = new
                    group_size += 1
                    continue
                else:
                    last_planet_with_letter = None
                    group_size = None

            new = cls._random_planet()
            if new.letter is not None:
                last_planet_with_letter = new
                group_size = 1
                max_group_size = random.randrange(1, 5)

            ret.append(new)

        return ret

    def __init__(self, name="", number=None, letter=None):
        self._name = name
        self._number = number
        self._letter = letter
        self._visited = False
        self._discovery_day = 1
        self._items = ItemCollection()
        self._samples_today = []

    def neighbour(self):
        name = self._name
        number = self._number
        letter = self._letter

        if letter:
            return Planet(name, number, chr(ord(letter) + 1))

        if number:
            return Planet(name, number + 1, letter)

        if random.randrange(0, 100) < 50:
            # Add letter
            letter = random_planet_letter()
        else:
            # Add number
            number = random_planet_number()

        return Planet(name, number, letter)

    def clear_samples_today(self):
        self._samples_today = []

    @property
    def samples_today(self):
        return self._samples_today

    @property
    def discovery_day(self):
        return self._discovery_day

    @discovery_day.setter
    def discovery_day(self, val):
        self._discovery_day = val

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, val):
        self._items = val

    @property
    def visited(self):
        return self._visited

    @visited.setter
    def visited(self, val):
        self._visited = val

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number

    @property
    def letter(self):
        return self._letter

    @property
    def full_name(self):
        ret = self._name
        if self._number is not None:
            ret += " %d" % self._number

        if self._letter is not None:
            ret += " %s" % self._letter

        return ret[0].upper() + ret[1:]
