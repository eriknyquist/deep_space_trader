import os

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

def shineImageIndex(planetname):
    return (ord(planetname[-2]) * len(planetname)) % 4

def hasRing(planetname):
    return bool((ord(planetname[-1]) * len(planetname)) % 2)

def planetNameToColors(planetname):
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
    def __init__(self, parent):
        super(PlanetImage, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.planetLabel = QtWidgets.QLabel()
        self.planetLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.pixmap = QtGui.QPixmap(WIDTH, HEIGHT)

        self.painter = QtGui.QPainter(self.pixmap)
        self.bg_image = QtGui.QPixmap(planet_background).scaled(WIDTH, HEIGHT)
        self.fill_image = QtGui.QPixmap(planet_fill).scaled(WIDTH, HEIGHT)
        self.outline_image = QtGui.QPixmap(planet_outline).scaled(WIDTH, HEIGHT)
        self.ring_image = QtGui.QPixmap(planet_ring).scaled(WIDTH, HEIGHT)

        self.shine_images = [
            QtGui.QPixmap(planet_shine_1).scaled(WIDTH, HEIGHT),
            QtGui.QPixmap(planet_shine_2).scaled(WIDTH, HEIGHT),
            QtGui.QPixmap(planet_shine_3).scaled(WIDTH, HEIGHT),
            QtGui.QPixmap(planet_shine_4).scaled(WIDTH, HEIGHT),
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

        for i in range(WIDTH):
            for j in range(HEIGHT):
                c = ret.pixelColor(i, j)
                if c.alpha() > 0:
                    ret.setPixelColor(i, j, color)
                else:
                    if alpha_white:
                        ret.setPixelColor(i, j, QtGui.QColor(255, 255, 255))

        return ret

    def setPlanetColors(self, bg_color, outline_color, fill_color, shine_color,
                        ring_color=None):
        planet = self.parent.state.current_planet
        shine_image = self.shine_images[shineImageIndex(planet.full_name)]
        self.painter.drawImage(0, 0, self.changeColor(self.bg_image, bg_color, alpha_white=True))
        self.painter.drawImage(0, 0, self.changeColor(self.outline_image, outline_color))
        self.painter.drawImage(0, 0, self.changeColor(self.fill_image, fill_color))
        self.painter.drawImage(0, 0, self.changeColor(shine_image, shine_color))

        if ring_color is not None:
            self.painter.drawImage(0, 0, self.changeColor(self.ring_image, ring_color))

        self.planetLabel.setPixmap(self.pixmap)
