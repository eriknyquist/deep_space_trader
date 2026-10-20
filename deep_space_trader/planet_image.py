"""
Pictures of planets, drawn from their names: the same name always gives the
same picture, on any computer, every time the game runs (different names can
give the same picture, which is fine).

The name is turned into a number (with SHA-256), which seeds a random number
generator, and every choice about the picture (colours, rings, moons, stars...)
is taken from it, in a fixed order. Only random.Random.random() is used, since
Python guarantees that it gives the same numbers for the same seed in every
version (other methods, like randint() and choice(), may change)
"""
import hashlib
import math
import random

import numpy

from PyQt5 import QtWidgets, QtCore, QtGui

# Size of the current planet's picture in the information section, in pixels
WIDTH = 72
HEIGHT = 72

# Pictures are drawn on a 100x100 grid, and scaled to the size they're shown at
GRID = 100.0


class SeededChoices(object):
    """
    Random choices from a seed, made only with random.Random.random()
    """
    def __init__(self, seed):
        self._random = random.Random(seed)

    def fraction(self):
        return self._random.random()

    def uniform(self, low, high):
        return low + (high - low) * self._random.random()

    def chance(self, probability):
        return self._random.random() < probability

    def index(self, count):
        return min(count - 1, int(self._random.random() * count))


def planetSeed(name):
    """
    A number from a planet's name, the same on every computer and every run
    (unlike Python's hash(), which changes every time Python starts)
    """
    return int.from_bytes(hashlib.sha256(name.encode("utf-8")).digest()[:8], "big")


def colorHex(hue, saturation, value):
    return QtGui.QColor.fromHsvF(hue % 1.0, saturation, value).name()


def planetRecipe(name):
    """
    Everything about a planet's picture, chosen from its name: a dictionary of
    numbers and colours (e.g. "#3a7bd5"), with positions and sizes on a
    100x100 grid. Every value is taken from the seed in a fixed order, so
    changing the order (or adding a choice anywhere but at the end of a
    section) changes every planet's picture
    """
    choose = SeededChoices(planetSeed(name))
    recipe = {}

    # Background: dark space, tinted a little, with stars
    hue = choose.fraction()
    recipe["space"] = colorHex(hue, choose.uniform(0.3, 0.7), choose.uniform(0.05, 0.12))
    stars = []
    for _ in range(int(choose.uniform(18, 40))):
        stars.append((choose.uniform(0, GRID), choose.uniform(0, GRID),   # position
                      choose.uniform(0.3, 0.9),                         # radius
                      choose.uniform(0.35, 1.0)))                       # brightness
    recipe["stars"] = stars

    # Sometimes a faint cloud of coloured gas behind everything
    recipe["nebula"] = None
    if choose.chance(0.3):
        recipe["nebula"] = (choose.uniform(15, 85), choose.uniform(15, 85),   # centre
                            choose.uniform(30, 55),                         # radius
                            colorHex(choose.fraction(), choose.uniform(0.5, 0.9), 0.8))

    # Where the light comes from (an angle, in degrees: 0 is the right, 90 the top)
    recipe["light_angle"] = choose.uniform(0, 360)

    # A ring and a moon each need room around the planet, so whether there is
    # one decides how big the planet can be, so that everything fits
    has_ring = choose.chance(0.3)
    has_moon = choose.chance(0.5)
    if has_ring and has_moon:
        recipe["radius"] = choose.uniform(19, 21)
    elif has_ring:
        recipe["radius"] = choose.uniform(24, 28)
    elif has_moon:
        recipe["radius"] = choose.uniform(26, 31)
    else:
        recipe["radius"] = choose.uniform(27, 34)

    # Any colour, but not too dark to see against space, or too washed out
    recipe["color"] = colorHex(choose.fraction(), choose.uniform(0.25, 0.85), choose.uniform(0.55, 0.95))

    # A thin glowing atmosphere around the edge, sometimes
    recipe["atmosphere"] = None
    if choose.chance(0.5):
        recipe["atmosphere"] = colorHex(choose.fraction(), choose.uniform(0.2, 0.6), 1.0)

    recipe["ring"] = None
    if has_ring:
        recipe["ring"] = {
            "tilt": choose.uniform(-30, 30),           # degrees from horizontal
            "inner": choose.uniform(1.25, 1.4),        # times the planet's radius
            "outer": choose.uniform(1.55, 1.75),
            "flatness": choose.uniform(0.22, 0.38),    # height / width
            "color": colorHex(choose.fraction(), choose.uniform(0.15, 0.6), choose.uniform(0.7, 0.95)),
            "bands": int(choose.uniform(1, 4)),        # darker gaps in the ring
        }

    # A moon, clear of the planet (and of its ring), towards one of the corners,
    # where there's most room
    recipe["moon"] = None
    if has_moon:
        radius = choose.uniform(6.5, 8.5) if has_ring else choose.uniform(6.5, 10.5)
        reach = recipe["radius"] * (recipe["ring"]["outer"] if has_ring else 1.0)
        corner = 45 + 90 * choose.index(4)
        angle = corner + choose.uniform(-8, 8)
        distance = reach + radius + (choose.uniform(1.5, 3) if has_ring else choose.uniform(1.5, 4))

        # Moved in from the edges if it doesn't fit (the sizes above are chosen
        # so that it always does, but just in case)
        x = 50 + distance * math.cos(math.radians(angle))
        y = 50 - distance * math.sin(math.radians(angle))
        x = min(GRID - radius - 1, max(radius + 1, x))
        y = min(GRID - radius - 1, max(radius + 1, y))

        # (Rounded: cos() and sin() can differ in the last digits from one
        # computer to another, which is invisible, but would make the recipe differ)
        recipe["moon"] = (round(x, 3), round(y, 3), radius,
                          colorHex(choose.fraction(), choose.uniform(0.1, 0.45), choose.uniform(0.75, 0.95)))

    # How much of the planet (and moon) is lit, as seen from here: see _sphereImage.
    # (Chosen last, so that adding it didn't change the choices above)
    recipe["phase"] = choose.uniform(-0.2, 0.85)

    return recipe


def _sphereImage(pixels, color, light_angle, phase, night):
    """
    Picture of a lit ball, 'pixels' across (on a see-through background).
    Each pixel is lit by how much its bit of the ball's surface faces the
    light, so the line between day and night curves round the ball, and the
    lit side darkens towards its edges.

    'light_angle' is the direction the light comes from, across the picture (in
    degrees: 0 is the right, 90 the top), and 'phase' is how much it comes from
    in front, from -1 (from behind: all dark) to 1 (from in front: all lit). At
    0 exactly half is lit; below 0 the lit part is a crescent. 'night' is how
    dark the night side is, from 0 (not at all) to 255 (black)
    """
    # Position of each pixel's centre on the ball, from -1 to 1 (y up)
    steps = (numpy.arange(pixels) + 0.5) / pixels * 2.0 - 1.0
    x = steps[numpy.newaxis, :]
    y = -steps[:, numpy.newaxis]
    distance = numpy.sqrt(x * x + y * y)
    z = numpy.sqrt(numpy.clip(1.0 - x * x - y * y, 0.0, 1.0))

    # Direction of the light
    across = math.sqrt(1.0 - phase * phase)
    lx = across * math.cos(math.radians(light_angle))
    ly = across * math.sin(math.radians(light_angle))
    facing = x * lx + y * ly + z * phase

    # Day: brighter where the surface faces the light. Night: dark. In between,
    # a soft change from one to the other
    day = numpy.clip((facing + 0.1) / 0.3, 0.0, 1.0)
    day = day * day * (3.0 - 2.0 * day)
    day_shade = 0.6 + 0.55 * numpy.clip(facing, 0.0, 1.0)
    night_shade = (1.0 - night / 255.0) * 0.6
    shade = night_shade + (day_shade - night_shade) * day

    base = QtGui.QColor(color)
    rgb = numpy.stack([numpy.clip(c * shade, 0, 255) for c in (base.red(), base.green(), base.blue())], axis=-1)

    # Smooth edge: how much of each pixel the ball covers
    edge = numpy.clip((1.0 - distance) * pixels / 2.0 + 0.5, 0.0, 1.0)

    argb = numpy.empty((pixels, pixels), dtype=numpy.uint32)
    argb[:] = ((numpy.round(edge * 255).astype(numpy.uint32) << 24) |
               (rgb[..., 0].astype(numpy.uint32) << 16) |
               (rgb[..., 1].astype(numpy.uint32) << 8) |
               rgb[..., 2].astype(numpy.uint32))

    image = QtGui.QImage(argb.data, pixels, pixels, pixels * 4, QtGui.QImage.Format_ARGB32)
    return image.copy()   # (the numpy array is freed when this function returns)


def _shadedSphere(painter, centre, radius, color, light_angle, phase, night=175):
    """
    A lit ball (see _sphereImage), drawn at the painter's full resolution
    """
    scale = painter.transform().m11()
    pixels = max(2, int(math.ceil(radius * 2 * scale)))
    rect = QtCore.QRectF(centre.x() - radius, centre.y() - radius, radius * 2, radius * 2)
    painter.drawImage(rect, _sphereImage(pixels, color, light_angle, phase, night))


def _ringPath(recipe, front_only=False):
    """
    The ring around the planet (centred on 0, 0, before tilting): an
    elliptical band, or only its front half (the half nearer to us, which
    passes in front of the planet)
    """
    ring = recipe["ring"]
    radius = recipe["radius"]
    flat = ring["flatness"]
    outer, inner = radius * ring["outer"], radius * ring["inner"]

    path = QtGui.QPainterPath()
    path.addEllipse(QtCore.QPointF(0, 0), outer, outer * flat)
    hole = QtGui.QPainterPath()
    hole.addEllipse(QtCore.QPointF(0, 0), inner, inner * flat)
    path = path.subtracted(hole)

    if front_only:
        front = QtGui.QPainterPath()
        front.addRect(QtCore.QRectF(-outer - 1, 0, (outer + 1) * 2, outer + 1))
        path = path.intersected(front)

    return path


def _drawRing(painter, recipe, front_only):
    ring = recipe["ring"]
    radius = recipe["radius"]
    color = QtGui.QColor(ring["color"])

    painter.save()
    painter.translate(50, 50)
    painter.rotate(-ring["tilt"])
    painter.setClipPath(_ringPath(recipe, front_only))

    # The band, a little see-through, with darker gaps
    color.setAlpha(210)
    painter.fillPath(_ringPath(recipe), color)
    inner, outer = radius * ring["inner"], radius * ring["outer"]
    gap = QtGui.QColor(ring["color"]).darker(160)
    gap.setAlpha(170)
    pen = QtGui.QPen(gap, 0.8)
    painter.setPen(pen)
    painter.setBrush(QtCore.Qt.NoBrush)
    for i in range(1, ring["bands"] + 1):
        r = inner + (outer - inner) * i / (ring["bands"] + 1.0)
        painter.drawEllipse(QtCore.QPointF(0, 0), r, r * ring["flatness"])

    painter.restore()


def drawSpace(painter, recipe):
    """
    Draw the space behind a planet (see planetRecipe), on a 100x100 grid:
    stars, and maybe a nebula
    """
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtCore.Qt.NoPen)
    painter.fillRect(QtCore.QRectF(0, 0, GRID, GRID), QtGui.QColor(recipe["space"]))
    if recipe["nebula"] is not None:
        x, y, radius, color = recipe["nebula"]
        gradient = QtGui.QRadialGradient(QtCore.QPointF(x, y), radius)
        inside = QtGui.QColor(color)
        inside.setAlpha(55)
        outside = QtGui.QColor(color)
        outside.setAlpha(0)
        gradient.setColorAt(0.0, inside)
        gradient.setColorAt(1.0, outside)
        painter.fillRect(QtCore.QRectF(0, 0, GRID, GRID), QtGui.QBrush(gradient))

    for x, y, radius, brightness in recipe["stars"]:
        painter.setBrush(QtGui.QColor(255, 255, 255, int(255 * brightness)))
        painter.drawEllipse(QtCore.QPointF(x, y), radius, radius)


def drawPlanet(painter, recipe, background=True):
    """
    Draw a planet from its recipe (see planetRecipe), on a 100x100 grid. With
    'background' False, only the planet (and its ring and moon), with no space behind
    """
    if background:
        drawSpace(painter, recipe)

    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtCore.Qt.NoPen)
    centre = QtCore.QPointF(50, 50)
    radius = recipe["radius"]

    # The whole ring first; the planet then hides its back half
    if recipe["ring"] is not None:
        _drawRing(painter, recipe, front_only=False)

    # Atmosphere: a soft glow just outside the edge
    if recipe["atmosphere"] is not None:
        glow = QtGui.QRadialGradient(centre, radius * 1.18)
        color = QtGui.QColor(recipe["atmosphere"])
        edge = radius / (radius * 1.18)
        for stop, alpha in ((edge - 0.02, 150), (edge, 120), (1.0, 0)):
            color.setAlpha(alpha)
            glow.setColorAt(stop, color)
        painter.setBrush(QtGui.QBrush(glow))
        painter.drawEllipse(centre, radius * 1.18, radius * 1.18)

    _shadedSphere(painter, centre, radius, recipe["color"], recipe["light_angle"], recipe["phase"])

    # The front half of the ring, over the planet
    if recipe["ring"] is not None:
        _drawRing(painter, recipe, front_only=True)

    if recipe["moon"] is not None:
        x, y, moon_radius, color = recipe["moon"]
        # (With a lighter night side than the planet's, so the moon stands out from space)
        _shadedSphere(painter, QtCore.QPointF(x, y), moon_radius, color, recipe["light_angle"], recipe["phase"],
                      night=120)


def planetPixmap(name, size, dpr=1.0):
    """
    Picture of the planet called 'name', 'size' pixels across. 'dpr' is the
    screen's device pixel ratio, so the picture is sharp on high-DPI screens
    """
    pixels = int(math.ceil(size * dpr))
    pixmap = QtGui.QPixmap(pixels, pixels)
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.scale(pixels / GRID, pixels / GRID)
    drawPlanet(painter, planetRecipe(name))
    painter.end()
    return pixmap


class PlanetImage(QtWidgets.QWidget):
    """
    Shows a picture of the current planet (see planetPixmap)
    """
    def __init__(self, parent):
        super(PlanetImage, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.planetLabel = QtWidgets.QLabel()
        self.planetLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.planetLabel.setFixedSize(WIDTH, HEIGHT)
        self.mainLayout.addWidget(self.planetLabel)

        self.update()

    def update(self):
        planet = self.parent.state.current_planet
        self.pixmap = planetPixmap(planet.full_name, WIDTH, self.devicePixelRatioF())
        self.planetLabel.setPixmap(self.pixmap)
        super(PlanetImage, self).update()
