import os

import numpy

from deep_space_trader.utils import IMAGE_DIR

from PyQt5 import QtWidgets, QtCore, QtGui

WIDTH = 50
HEIGHT = 50

planet_outline = os.path.join(IMAGE_DIR, 'planet_outline.png')
planet_ring = os.path.join(IMAGE_DIR, 'planet_ring.png')
planet_fill = os.path.join(IMAGE_DIR, 'planet_fill.png')
planet_background = os.path.join(IMAGE_DIR, 'planet_background.png')
planet_shine_1 = os.path.join(IMAGE_DIR, 'planet_shine_1.png')
planet_shine_2 = os.path.join(IMAGE_DIR, 'planet_shine_2.png')
planet_shine_3 = os.path.join(IMAGE_DIR, 'planet_shine_3.png')
planet_shine_4 = os.path.join(IMAGE_DIR, 'planet_shine_4.png')

# Template images, loaded once (on first use, since that needs a QApplication)
_templates = {}

def templateImage(filename):
    if filename not in _templates:
        _templates[filename] = QtGui.QPixmap(filename).scaled(WIDTH, HEIGHT)

    return _templates[filename]

def shineImageIndex(planetname):
    return (ord(planetname[-2]) * len(planetname)) % 4

def hasRing(planetname):
    return bool((ord(planetname[-1]) * len(planetname)) % 2)

def planetNameToColors(planetname):
    """
    Picks the colors for the planet image template (5 colors in total) based on
    the planet's name. Derives the RGB values for the colors from the numerical
    character values in the planet name string, so the same color scheme is always
    guaranteed for the same planet name.
    """
    i = 0
    rgbbuf = []
    ret = []
    has_ring = hasRing(planetname)
    num_colors = 4 + int(has_ring)

    for j in range(num_colors):
        for _ in range(3):
            b = planetname[i]
            rgbbuf.append((ord(b) * len(planetname)) % 255)

            i = (i + 1) % len(planetname)

        ret.append(QtGui.QColor(*rgbbuf))
        rgbbuf = []

    return tuple(ret)

class PlanetImage(QtWidgets.QWidget):
    """
    Draws an image of the current planet, with "unique" (not really truly unique but close enough)
    colours based on the planet name
    """
    def __init__(self, parent):
        super(PlanetImage, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.planetLabel = QtWidgets.QLabel()
        self.planetLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.pixmap = QtGui.QPixmap(WIDTH, HEIGHT)

        self.bg_image = templateImage(planet_background)
        self.fill_image = templateImage(planet_fill)
        self.outline_image = templateImage(planet_outline)
        self.ring_image = templateImage(planet_ring)

        self.shine_images = [
            templateImage(planet_shine_1),
            templateImage(planet_shine_2),
            templateImage(planet_shine_3),
            templateImage(planet_shine_4),
        ]

        self.update()
        self.mainLayout.addWidget(self.planetLabel)

        self.resize(self.pixmap.width(), self.pixmap.height())

    def update(self):
        planet = self.parent.state.current_planet
        colors = planetNameToColors(planet.full_name)
        self.setPlanetColors(*colors)
        super(PlanetImage, self).update()

    def changeColor(self, image, color, alpha_white=False):
        ret = image.toImage()
        if color is None:
            return ret

        # Every pixel that isn't fully transparent becomes 'color' (and with
        # alpha_white, every one that is becomes white). Done with numpy on the
        # image's pixels (0xAARRGGBB each), since a Python loop over them is slow
        ret = ret.convertToFormat(QtGui.QImage.Format_ARGB32)
        bits = ret.bits()
        bits.setsize(ret.sizeInBytes())
        pixels = numpy.frombuffer(bits, numpy.uint32).reshape(ret.height(), -1)[:, :ret.width()]
        visible = (pixels >> 24) > 0
        pixels[visible] = color.rgba()
        if alpha_white:
            pixels[~visible] = 0xFFFFFFFF

        return ret

    def setPlanetColors(self, bg_color, outline_color, fill_color, shine_color,
                        ring_color=None):
        planet = self.parent.state.current_planet
        shine_image = self.shine_images[shineImageIndex(planet.full_name)]

        # Only paint while drawing: a QPainter left active on the pixmap can crash
        # when Python frees the two in the wrong order
        painter = QtGui.QPainter(self.pixmap)
        painter.drawImage(0, 0, self.changeColor(self.bg_image, bg_color, alpha_white=True))
        painter.drawImage(0, 0, self.changeColor(self.outline_image, outline_color))
        painter.drawImage(0, 0, self.changeColor(self.fill_image, fill_color))
        painter.drawImage(0, 0, self.changeColor(shine_image, shine_color))

        if ring_color is not None:
            painter.drawImage(0, 0, self.changeColor(self.ring_image, ring_color))

        painter.end()
        self.planetLabel.setPixmap(self.pixmap)
