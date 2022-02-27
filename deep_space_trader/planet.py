import copy
import time
import random

from deep_space_trader.items import ItemCollection


def random_planet_number():
    return random.randrange(2, 399)

def random_planet_letter():
    return chr(random.randrange(97, 108))


class Planet(object):
    """
    Planet names are randomly generated using word parts from 3-dimensional array
    Planet.parts. Planet name will be one of two forms;

    Two-part name:

        random.choice(Planet.parts[0]) + random.choice(Planet.parts[2])

    Three-part name:

        random.choice(Planet.parts[0]) + random.choice(Planet.parts[1]) + random.choice(Planet.parts[2])

    Whether to use a two-part or three-part name is randomly decided for each planet
    name generated.
    """
    parts = [
        [
            'ha', 'he', 'hi', 'ho', 'hu', 'ca', 'ce', 'ci', 'co', 'cu',
            'sa', 'se', 'si', 'so', 'su', 'ja', 'ji', 'je', 'jo', 'ju', 'an',
            'pa', 'pe', 'pi', 'po', 'pu', 'ta', 'te', 'ti', 'to', 'tu',
            'kle', 'ke', 'ki', 'ko', 'ku', 'sha', 'she', 'shi', 'sho', 'shu',
            'hor', 'cer', 'cur', 'her', 'hur', 'sar', 'arn', 'irn', 'kler',
            'ka', 'la', 'nar', 'kar', 'bar', 'dar', 'blar', 'ger', 'yur',
            'zor', 'for', 'wor', 'gor', 'noth', 'roth', 'moth', 'zoth',
            'loth', 'nith', 'lith', 'sith', 'dith', 'ith', 'oth', 'orb', 'urb',
            'er', 'zer', 'ze', 'zera', 'ter', 'nor', 'za', 'zi', 'di', 'mi',
            'per', 'pir', 'pera', 'par', 'sta', 'mor', 'kur', 'ker', 'ni'
            'ler', 'der', 'ber', 'shar', 'sher', 'mer', 'wer', 'fer', 'fra'
            'gra', 'bra', 'zir', 'dir', 'tir', 'sir', 'mir', 'nir', 'por',
            'lir', 'bir', 'dra', 'tha', 'the', 'tho'
        ],
        [
            'ta', 'te', 'ti', 'to', 'tu', 'ba', 'be', 'bi', 'bo', 'tis', 'ris',
            'beur', 'bu', 'cu', 'lur', 'mur', 'da', 'de', 'di', 'do', 'ka',
            'ke', 'ki', 'ko', 'ku', 'la', 'le', 'li', 'lo', 'lu', 'loo', 'koo',
            'lee', 'kee', 'du', 'lor', 'der', 'ser', 'per', 'fu', 'fer', 'ler',
            'zer', 'wi', 'na', 'ne', 'no', 'noo', 'ra', 'ri', 'ro', 'roo', 'va',
            've', 'vi', 'vo', 'vu', 'bre', 'dre', 'pre', 'tre', 're', 'ge',
            'ga', 'gu', 'mu', 'nu', 'ru', 'mi', 'ni', 'su', 'fa', 'fe', 'fi',
            'fo', 'fis', 'sa', 'se', 'si', 'so', 'pa', 'pe', 'pi', 'po', 'pu',
            'ma', 'me', 'mo', 'moo', 'mee', 'see', 'pee', 'nee'
        ],
        [
            'res', 'lia', 'gese', 'naise', 'bler', 'pler', 'teres', 'tere',
            'ter', 'pules', 'ner', 'yer', 'prer', 'padia', 'dium', 'dum', 'rem',
            'tem', 'dem', 'ratis', 'cus', 'tus', 'rus', 'muth', 'yuth', 'reth',
            'doth', 'rath', 'bath', 'tath', 'path', 'sadia', 'adia', 'radia',
            'anus', 'nus', 'ban', 'tan', 'lan', 'dan', 'man', 'nan', 'xan',
            'zan', 'pan', 'ius', 'rious', 'tius', 'bius', 'sius', 'sise',
            'suse', 'pus', 'dus', 'mus', 'bus', 'puth', 'suth', 'duth', 'tuth',
            'na', 'da', 'tair', 'taire', 'fair', 'tare', 'tar', 'bar', 'lar',
            'kar', 'thar', 'mar', 'to', 'ko', 'ba', 'ta', 'sha', 'ra', 'wa',
            'ka', 'ni', 'di', 'bi', 'ti', 'shi', 'ri', 'la', 'le', 'li', 'lo',
            'lu', 'car', 'dar', 'far', 'gar', 'har', 'jar', 'nar', 'par', 'rar',
            'sar', 'var'
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
    def _random_planet(cls, long_name_prob=50, number_suffix_prob=35, letter_suffix_prob=35):
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
        self._resists_destruction = False
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
    def resists_destruction(self):
        return self._resists_destruction

    @resists_destruction.setter
    def resists_destruction(self, val):
        self._resists_destruction = val

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
