import hashlib
import json
import math
import random

import pytest
from PyQt5 import QtGui

from deep_space_trader import planet_image
from deep_space_trader.planet import Planet
from deep_space_trader.planet_image import planetRecipe, planetPixmap, SeededChoices


def fingerprint(recipe):
    """
    Short summary of a whole recipe. Numbers are rounded, so that differences
    in the last digits between computers don't count
    """
    def rounded(value):
        if isinstance(value, float):
            return round(value, 6)
        if isinstance(value, (list, tuple)):
            return [rounded(v) for v in value]
        if isinstance(value, dict):
            return {k: rounded(v) for k, v in value.items()}
        return value

    return hashlib.sha256(json.dumps(rounded(recipe), sort_keys=True).encode()).hexdigest()[:16]


def some_names(count=300):
    state = random.getstate()
    random.seed(1234)
    names = [p.full_name for p in Planet.random(num=count, used_names=set())]
    random.setstate(state)
    return names


def test_same_name_same_recipe(qapp):
    for name in some_names(50):
        assert planetRecipe(name) == planetRecipe(name)


def test_recipes_never_change(qapp):
    # The most important rule: a planet always looks the same, on every
    # computer, in every version of the game. If this fails, a change to
    # planetRecipe has changed every planet's picture
    recipe = planetRecipe("Kandar 12 c")
    assert recipe["color"] == "#9c7248"
    assert recipe["atmosphere"] is None
    assert recipe["ring"]["color"] == "#ca9d63"
    assert recipe["moon"] is not None
    assert len(recipe["stars"]) == 33
    assert recipe["light_angle"] == pytest.approx(321.1279389553688)
    assert recipe["phase"] == pytest.approx(-0.044026730129961555)

    assert {name: fingerprint(planetRecipe(name)) for name in
            ("Kandar 12 c", "Pordoth 48", "Sithrifuan 301", "Zijuan 133 g")} == {
        "Kandar 12 c": "1dba1539f13e645c",
        "Pordoth 48": "2fab95dd8f976e3a",
        "Sithrifuan 301": "59f90c5f1c3d6029",
        "Zijuan 133 g": "cc77b20c4ffd7b4e",
    }


def test_names_give_varied_pictures(qapp):
    recipes = [planetRecipe(name) for name in some_names()]
    assert len({r["color"] for r in recipes}) > 250
    for feature, low, high in (("ring", 0.2, 0.4), ("moon", 0.4, 0.6), ("atmosphere", 0.4, 0.6),
                               ("nebula", 0.2, 0.4)):
        share = sum(r[feature] is not None for r in recipes) / float(len(recipes))
        assert low < share < high, feature


def test_everything_fits_in_the_picture(qapp):
    for name in some_names():
        recipe = planetRecipe(name)
        radius = recipe["radius"]
        reach = radius * (recipe["ring"]["outer"] if recipe["ring"] else 1.0)
        assert reach <= 50

        if recipe["moon"] is not None:
            x, y, moon_radius, _ = recipe["moon"]
            assert moon_radius <= x <= 100 - moon_radius
            assert moon_radius <= y <= 100 - moon_radius
            # Not in front of the planet
            assert math.hypot(x - 50, y - 50) >= radius + moon_radius

        # Never too dark to see against space
        assert QtGui.QColor(recipe["color"]).valueF() >= 0.5
        assert QtGui.QColor(recipe["space"]).valueF() <= 0.15


def test_seeded_choices_stay_in_range():
    choose = SeededChoices(42)
    for _ in range(1000):
        assert 3 <= choose.uniform(3, 7) < 7
        assert 0 <= choose.index(5) <= 4
    assert not any(SeededChoices(1).chance(0.0) for _ in range(100))


def test_seed_is_not_pythons_hash():
    # hash() of a string changes every time Python starts
    assert planet_image.planetSeed("Kandar 12 c") == planet_image.planetSeed("Kandar 12 c")
    assert planet_image.planetSeed("Kandar 12 c") == 0x1ec7ad483d616b8a


@pytest.mark.parametrize("dpr", [1.0, 2.0])
def test_pixmap_size(qapp, dpr):
    pixmap = planetPixmap("Pordoth 48", 72, dpr)
    assert (pixmap.width(), pixmap.height()) == (72 * dpr, 72 * dpr)
    assert pixmap.devicePixelRatio() == dpr

    # Space fills the corners (no see-through background)
    image = pixmap.toImage()
    assert QtGui.qAlpha(image.pixel(0, 0)) == 255


def test_picture_follows_the_current_planet(game):
    image = game.infoBar.planetImage
    first = image.pixmap.toImage()
    game.state.current_planet = next(p for p in game.state.planets if p is not game.state.current_planet)
    game.infoBar.update()
    assert image.pixmap.toImage() != first


def brightness(image, x, y):
    return QtGui.QColor(image.pixel(x, y)).value()


def test_shading_curves_round_the_ball(qapp):
    from deep_space_trader.planet_image import _sphereImage
    white = "#ffffff"

    # Light from the right, half lit: dark on the left, lit on the right
    image = _sphereImage(100, white, 0, 0.0, 255)
    assert brightness(image, 20, 50) < 20 < 200 < brightness(image, 80, 50)

    # Light partly from in front: more than half lit, so the middle is lit,
    # and the line between day and night curves (it's further left in the
    # middle than near the top)
    image = _sphereImage(100, white, 0, 0.6, 255)
    assert brightness(image, 50, 50) > 150
    assert brightness(image, 30, 50) > brightness(image, 30, 12)

    # Light partly from behind: a crescent, with the middle dark
    image = _sphereImage(100, white, 0, -0.6, 255)
    assert brightness(image, 50, 50) < 20
    assert brightness(image, 95, 50) > 100

    # See-through outside the ball, with a smooth edge
    assert QtGui.qAlpha(image.pixel(0, 0)) == 0
    assert QtGui.qAlpha(image.pixel(50, 0)) < 255
    assert QtGui.qAlpha(image.pixel(50, 50)) == 255
