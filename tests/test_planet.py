import random

import pytest

from deep_space_trader.planet import Planet
from deep_space_trader.items import ItemCollection

from helpers import give


def test_full_name_formats():
    assert Planet("kandar").full_name == "Kandar"
    assert Planet("kandar", 12).full_name == "Kandar 12"
    assert Planet("kandar", 12, "c").full_name == "Kandar 12 c"


def test_neighbour_of_lettered_planet_is_next_letter():
    assert Planet("kandar", 12, "c").neighbour().full_name == "Kandar 12 d"


def test_neighbour_of_numbered_planet_is_next_number():
    assert Planet("kandar", 12).neighbour().full_name == "Kandar 13"


def test_neighbour_of_plain_planet_gets_a_number_or_letter():
    random.seed(3)
    for _ in range(20):
        neighbour = Planet("kandar").neighbour()
        assert neighbour.name == "kandar"
        assert (neighbour.number is not None) or (neighbour.letter is not None)


def test_name_parts_are_separate():
    # Bug 13: missing commas joined 'ni' + 'ler' and 'fra' + 'gra' into one part
    first_parts = Planet.parts[0]
    for part in ("ni", "ler", "fra", "gra"):
        assert part in first_parts
    assert "niler" not in first_parts
    assert "fragra" not in first_parts


def test_name_parts_have_no_duplicates():
    for parts in Planet.parts:
        assert len(parts) == len(set(parts))


def test_num_possible_planets():
    p0, p1, p2 = (len(p) for p in Planet.parts)
    assert Planet.num_possible_planets() == (p0 * p1 * p2) + (p0 * p2)


def test_random_planets_have_unique_names():
    # Bug 15: names used to repeat often in large batches
    random.seed(1)
    used = set()
    planets = []
    for _ in range(5):
        planets += Planet.random(num=2000, used_names=used)

    names = [p.full_name for p in planets]
    assert len(names) == 10000
    assert len(set(names)) == len(names)
    assert used == set(names)


def test_random_planets_avoid_names_already_used():
    random.seed(2)
    first = Planet.random(num=500)
    used = {p.full_name for p in first}
    taken = set(used)

    second = Planet.random(num=500, used_names=used)
    assert not taken & {p.full_name for p in second}


def test_random_planets_include_lettered_groups():
    random.seed(4)
    planets = Planet.random(num=2000)
    lettered = [p for p in planets if p.letter is not None]
    assert lettered, "expected some planets with a letter suffix"

    # Groups are consecutive letters of the same name and number
    for a, b in zip(planets, planets[1:]):
        if (a.letter is not None) and (b.letter is not None) and (a.name, a.number) == (b.name, b.number):
            assert ord(b.letter) == ord(a.letter) + 1


@pytest.mark.parametrize("days", [1, 5])
def test_update_prices_adds_one_history_entry_per_day(days):
    planet = Planet("kandar")
    give(planet.items, "tin", 1000)
    history = planet.items.items["tin"].value_history
    start = len(history)

    planet.update_prices(days + 1)
    assert len(history) == start + days

    # Already up to date for this day: nothing more is added
    planet.update_prices(days + 1)
    assert len(history) == start + days


def test_new_planet_has_no_items_and_is_unvisited():
    planet = Planet("kandar")
    assert isinstance(planet.items, ItemCollection)
    assert planet.items.count() == 0
    assert not planet.visited
    assert not planet.resists_destruction
