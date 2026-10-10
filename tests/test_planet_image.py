from PyQt5 import QtGui

from deep_space_trader import planet_image
from deep_space_trader.planet_image import PlanetImage


def recoloured_slowly(image, color, alpha_white):
    """
    The original pixel-by-pixel version of PlanetImage.changeColor
    """
    ret = image.toImage()
    for i in range(planet_image.WIDTH):
        for j in range(planet_image.HEIGHT):
            if ret.pixelColor(i, j).alpha() > 0:
                ret.setPixelColor(i, j, color)
            elif alpha_white:
                ret.setPixelColor(i, j, QtGui.QColor(255, 255, 255))

    return ret


def argb(image):
    return image.convertToFormat(QtGui.QImage.Format_ARGB32)


TEMPLATES = [
    planet_image.planet_background, planet_image.planet_outline, planet_image.planet_fill,
    planet_image.planet_ring, planet_image.planet_shine_1, planet_image.planet_shine_2,
    planet_image.planet_shine_3, planet_image.planet_shine_4,
]


def change_color(image, color, alpha_white=False):
    # changeColor doesn't use the widget, so there's no need to make a game for it
    return PlanetImage.changeColor(None, image, color, alpha_white)


def test_recolouring_matches_pixel_by_pixel_version(qapp):
    color = QtGui.QColor(12, 200, 99)
    for filename in TEMPLATES:
        image = planet_image.templateImage(filename)
        for alpha_white in (False, True):
            expected = argb(recoloured_slowly(image, color, alpha_white))
            assert argb(change_color(image, color, alpha_white)) == expected, (filename, alpha_white)


def test_no_colour_leaves_image_alone(qapp):
    image = planet_image.templateImage(planet_image.planet_ring)
    assert change_color(image, None) == image.toImage()


def test_template_images_are_loaded_once(qapp):
    first = planet_image.templateImage(planet_image.planet_fill)
    assert planet_image.templateImage(planet_image.planet_fill).cacheKey() == first.cacheKey()
    assert (first.width(), first.height()) == (planet_image.WIDTH, planet_image.HEIGHT)
