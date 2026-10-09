import math

from deep_space_trader import constants as const
from deep_space_trader.utils import selectRowByKey, ICON_PATH
from deep_space_trader.i18n import formatNumber, formatDistance

from PyQt5 import QtWidgets, QtCore, QtGui


# Map scale
PIXELS_PER_LY = 10.0

# Dot sizes, in pixels (they stay the same size when zooming)
DOT_SIZE = 8
LARGE_DOT_SIZE = 12
CURRENT_DOT_SIZE = 14

# Ring around the current planet, in pixels
CURRENT_RING_SIZE = 24

# The mouse picks the nearest planet within this many pixels, so small dots are easy to hit
PICK_RADIUS = 10

# How much each scroll wheel step zooms in or out
ZOOM_STEP = 1.25

# Size of the cells used to find planets near the mouse quickly, in light-years
GRID_CELL_LY = 10.0

BACKGROUND_COLOR = QtGui.QColor("#101010")
# The current planet is yellow, so it stands out from the green previous planets
CURRENT_COLOR = QtGui.QColor("#ffd633")
LABEL_COLOR = QtGui.QColor("#ffffff")
PREVIOUS_COLORS = [QtGui.QColor(0, 0xAA, 0, 200), QtGui.QColor(0, 0xAA, 0, 110)]
HOME_COLOR = QtGui.QColor("#3399ff")
VISITED_COLOR = QtGui.QColor("#bbbbbb")
UNVISITED_COLOR = QtGui.QColor("#888888")
SELECTED_COLOR = QtGui.QColor("#ffffff")
RANGE_COLOR = QtGui.QColor(255, 255, 255, 40)

# Width of the ring drawn for planets not visited yet, in pixels
UNVISITED_RING_WIDTH = 1.5

# Opacity of planets that don't match the planets search box
DIMMED_OPACITY = 0.2


class DotStyle(object):
    """
    How one planet is drawn: a dot 'size' pixels across, filled with 'fill'
    (None for hollow), with a ring of colour 'ring' (None for no ring), and
    optionally a larger ring 'outer_ring' around it
    """
    def __init__(self, fill=None, ring=None, size=DOT_SIZE, ring_width=UNVISITED_RING_WIDTH,
                 outer_ring=None, opacity=1.0):
        self.fill = fill
        self.ring = ring
        self.size = size
        self.ring_width = ring_width
        self.outer_ring = outer_ring
        self.opacity = opacity


def scenePos(planet):
    """
    Where a planet is on the map (north is up)
    """
    return QtCore.QPointF(planet.x * PIXELS_PER_LY, -planet.y * PIXELS_PER_LY)


def dotSprite(fill, ring, dpr):
    """
    Small picture of a planet's dot, drawn once and then copied for each planet:
    copying it thousands of times is much faster than drawing thousands of dots.
    'dpr' is the screen's device pixel ratio, so the dot is sharp on high-DPI screens
    """
    size = DOT_SIZE + 2
    sprite = QtGui.QPixmap(int(math.ceil(size * dpr)), int(math.ceil(size * dpr)))
    sprite.setDevicePixelRatio(dpr)
    sprite.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(sprite)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    centre = QtCore.QPointF(size / 2.0, size / 2.0)
    r = DOT_SIZE / 2.0

    if fill is not None:
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(fill)
        painter.drawEllipse(centre, r, r)

    if ring is not None:
        painter.setPen(QtGui.QPen(ring, UNVISITED_RING_WIDTH))
        painter.setBrush(QtCore.Qt.NoBrush)
        ring_r = r - UNVISITED_RING_WIDTH / 2.0
        painter.drawEllipse(centre, ring_r, ring_r)

    painter.end()
    return sprite


def drawDot(painter, centre, style):
    """
    Draw one planet's dot in the given DotStyle, centred on 'centre' (in pixels)
    """
    painter.setOpacity(style.opacity)

    if style.outer_ring is not None:
        painter.setPen(QtGui.QPen(style.outer_ring, 2))
        painter.setBrush(QtCore.Qt.NoBrush)
        r = CURRENT_RING_SIZE / 2.0
        painter.drawEllipse(centre, r, r)

    # Cover anything drawn underneath (e.g. the planet's ordinary dot)
    r = style.size / 2.0
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(BACKGROUND_COLOR)
    painter.drawEllipse(centre, r, r)

    if style.fill is not None:
        painter.setBrush(style.fill)
        painter.drawEllipse(centre, r, r)

    if style.ring is not None:
        painter.setPen(QtGui.QPen(style.ring, style.ring_width))
        painter.setBrush(QtCore.Qt.NoBrush)
        ring_r = r - style.ring_width / 2.0
        painter.drawEllipse(centre, ring_r, ring_r)


def legendIcon(style, dpr):
    """
    Picture of a dot for the legend: drawn exactly as on the map, on a small
    square of the map's dark background, so it looks right with either theme
    """
    size = CURRENT_RING_SIZE + 6
    icon = QtGui.QPixmap(int(math.ceil(size * dpr)), int(math.ceil(size * dpr)))
    icon.setDevicePixelRatio(dpr)
    icon.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(icon)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(BACKGROUND_COLOR)
    painter.drawRoundedRect(QtCore.QRectF(0, 0, size, size), 4, 4)
    drawDot(painter, QtCore.QPointF(size / 2.0, size / 2.0), style)
    painter.end()
    return icon


try:
    # Fast way to give drawPixmapFragments() thousands of positions at once, from
    # a numpy array (used by pyqtgraph's own scatter plots). It's an internal part
    # of pyqtgraph, so fall back to a slower Python loop if it isn't there
    import numpy
    from pyqtgraph.Qt.internals import PrimitiveArray
except ImportError:
    PrimitiveArray = None


class PlanetsLayer(QtWidgets.QGraphicsItem):
    """
    Draws every planet. Thousands of separate graphics items, or thousands of
    separately drawn dots, made zooming slow. Instead, every planet is drawn as
    a copy of a small pre-drawn dot (one drawPixmapFragments() call for all
    visited planets, and one for the rest), and the few special planets
    (current, home, previous, selected) are drawn on top, one by one
    """
    def __init__(self, starMap):
        super(PlanetsLayer, self).__init__()
        self.starMap = starMap
        state = starMap.parent.state

        # visited -> (x positions, y positions, opacities) of those planets, in scene coordinates
        groups = {True: ([], [], []), False: ([], [], [])}
        for planet in state.planets:
            xs, ys, opacities = groups[planet.visited]
            pos = scenePos(planet)
            xs.append(pos.x())
            ys.append(pos.y())
            opacities.append(DIMMED_OPACITY if starMap.isDimmed(planet) else 1.0)

        if PrimitiveArray is not None:
            self.groups = {visited: tuple(numpy.array(values, dtype=float) for values in group)
                           for visited, group in groups.items()}
            self.fragments = PrimitiveArray(QtGui.QPainter.PixmapFragment, 10)
        else:
            self.groups = {visited: (QtGui.QPolygonF([QtCore.QPointF(x, y) for x, y in zip(xs, ys)]), opacities)
                           for visited, (xs, ys, opacities) in groups.items()}

        self.sprites = {}
        self.spritesDpr = None

        # Leave room for the dots and rings around the outermost planets
        margin = 50 * PIXELS_PER_LY
        rect = QtGui.QPolygonF([scenePos(p) for p in state.planets]).boundingRect()
        self.rect = rect.adjusted(-margin, -margin, margin, margin)

    def boundingRect(self):
        return self.rect

    def spritesFor(self, dpr):
        if dpr != self.spritesDpr:
            self.sprites = {True: dotSprite(VISITED_COLOR, None, dpr), False: dotSprite(None, UNVISITED_COLOR, dpr)}
            self.spritesDpr = dpr

        return self.sprites

    def paint(self, painter, option, widget=None):
        transform = painter.transform()
        dpr = widget.devicePixelRatioF() if widget is not None else 1.0
        sprites = self.spritesFor(dpr)

        # Only planets that can be seen, plus a margin so dots at the edges are drawn
        visible = QtCore.QRectF(painter.viewport()).adjusted(-DOT_SIZE, -DOT_SIZE, DOT_SIZE, DOT_SIZE)

        painter.save()
        # Draw in pixels, so the dots don't change size with the zoom
        painter.resetTransform()
        for visited in (False, True):
            sprite = sprites[visited]
            if PrimitiveArray is not None:
                self.paintFast(painter, transform, visible, self.groups[visited], sprite, dpr)
            else:
                self.paintSlow(painter, transform, visible, self.groups[visited], sprite, dpr)

        painter.restore()

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        for planet in self.starMap.specialPlanets():
            self.paintSpecial(painter, planet)

        painter.setOpacity(1.0)

    def paintFast(self, painter, transform, visible, group, sprite, dpr):
        xs, ys, opacities = group
        x = transform.m11() * xs + transform.m21() * ys + transform.dx()
        y = transform.m12() * xs + transform.m22() * ys + transform.dy()
        shown = ((x >= visible.left()) & (x <= visible.right()) &
                 (y >= visible.top()) & (y <= visible.bottom()))
        count = int(numpy.count_nonzero(shown))
        if count == 0:
            return

        self.fragments.resize(count)
        fragments = self.fragments.ndarray()
        fragments[:, 0] = x[shown]                       # centre x
        fragments[:, 1] = y[shown]                       # centre y
        fragments[:, 2:6] = [0, 0, sprite.width(), sprite.height()]   # source rect, in sprite pixels
        fragments[:, 6:9] = [1.0 / dpr, 1.0 / dpr, 0.0]  # scale x, scale y, rotation
        fragments[:, 9] = opacities[shown]               # opacity
        painter.drawPixmapFragments(*self.fragments.drawargs(), sprite)

    def paintSlow(self, painter, transform, visible, group, sprite, dpr):
        points, opacities = group
        source = QtCore.QRectF(sprite.rect())
        create = QtGui.QPainter.PixmapFragment.create
        fragments = [create(point, source, 1.0 / dpr, 1.0 / dpr, 0, opacity)
                     for point, opacity in zip(transform.map(points), opacities)
                     if visible.contains(point)]

        if fragments:
            painter.drawPixmapFragments(fragments, sprite)

    def paintSpecial(self, painter, planet):
        centre = painter.transform().map(scenePos(planet))

        painter.save()
        # Draw in pixels, so the size doesn't change with the zoom
        painter.resetTransform()
        drawDot(painter, centre, self.starMap.planetStyle(planet))
        painter.restore()


class StarMapView(QtWidgets.QGraphicsView):
    """
    Shows the map, zooms with the scroll wheel, pans by dragging, and tells
    the StarMap when a planet is hovered over, clicked or double-clicked
    """
    def __init__(self, starMap):
        super(StarMapView, self).__init__()
        self.starMap = starMap
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(BACKGROUND_COLOR)

        # Needed to show planet names while the mouse moves, with no button pressed
        self.viewport().setMouseTracking(True)

    def planetAt(self, pos):
        """
        The planet nearest to 'pos' (in view coordinates), if it's within
        PICK_RADIUS pixels
        """
        radius = PICK_RADIUS / self.transform().m11()
        return self.starMap.planetNear(self.mapToScene(pos), radius)

    def wheelEvent(self, event):
        factor = ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / ZOOM_STEP
        self.scale(factor, factor)

    def mouseMoveEvent(self, event):
        self.starMap.planetHovered(self.planetAt(event.pos()))
        super(StarMapView, self).mouseMoveEvent(event)

    def viewportEvent(self, event):
        # Show the nearest planet's tooltip, even when the mouse isn't exactly on its dot
        if event.type() == QtCore.QEvent.ToolTip:
            planet = self.planetAt(event.pos())
            if planet is not None:
                QtWidgets.QToolTip.showText(event.globalPos(), self.starMap.tooltipText(planet), self.viewport())
            else:
                QtWidgets.QToolTip.hideText()
            return True

        return super(StarMapView, self).viewportEvent(event)

    def leaveEvent(self, event):
        self.starMap.planetHovered(None)
        super(StarMapView, self).leaveEvent(event)

    def mousePressEvent(self, event):
        planet = self.planetAt(event.pos())
        if (planet is not None) and (event.button() == QtCore.Qt.LeftButton):
            self.starMap.planetClicked(planet)

        super(StarMapView, self).mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        planet = self.planetAt(event.pos())
        if (planet is not None) and (event.button() == QtCore.Qt.LeftButton):
            self.starMap.planetDoubleClicked(planet)
            return

        super(StarMapView, self).mouseDoubleClickEvent(event)


class StarMap(QtWidgets.QDialog):
    """
    Map of all discovered planets, around the home planet
    """
    def __init__(self, parent):
        super(StarMap, self).__init__(parent)

        self.parent = parent
        self.selected = parent.locationBrowser.selectedPlanet()
        self.hovered = None
        self.hoverLabel = None
        self.currentLabel = None
        self.layer = None
        self.grid = {}
        self.matching = None

        self.scene = QtWidgets.QGraphicsScene(self)
        self.view = StarMapView(self)
        self.view.setScene(self.scene)

        legendLayout = QtWidgets.QHBoxLayout()
        legendLayout.addWidget(self.keyGroup(), 3)
        legendLayout.addWidget(self.controlsGroup(), 2)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(self.view)
        self.mainLayout.addLayout(legendLayout)
        self.setLayout(self.mainLayout)

        self.setWindowTitle(self.tr("Star map"))
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        self.build()
        self.fitToPlanets()

    def sizeHint(self):
        return QtCore.QSize(800, 650)

    def keyGroup(self):
        """
        Group box explaining what the dots mean, with each dot drawn as on the map
        """
        entries = [
            (self.tr("You are here"), DotStyle(fill=CURRENT_COLOR, size=CURRENT_DOT_SIZE, outer_ring=CURRENT_COLOR)),
            (self.tr("Previous planets"), DotStyle(fill=PREVIOUS_COLORS[0])),
            (self.tr("Home planet"), DotStyle(fill=VISITED_COLOR, ring=HOME_COLOR, ring_width=2.5,
                                              size=LARGE_DOT_SIZE)),
            (self.tr("Visited"), DotStyle(fill=VISITED_COLOR)),
            (self.tr("Not visited"), DotStyle(ring=UNVISITED_COLOR)),
            (self.tr("Selected"), DotStyle(ring=SELECTED_COLOR, ring_width=2.5)),
        ]

        dpr = self.devicePixelRatioF()
        layout = QtWidgets.QGridLayout()
        self.keyLabels = []
        columns = 3
        for i, (text, style) in enumerate(entries):
            icon = QtWidgets.QLabel()
            icon.setPixmap(legendIcon(style, dpr))
            label = QtWidgets.QLabel(text)
            self.keyLabels.append(label)
            row, column = divmod(i, columns)
            layout.addWidget(icon, row, column * 2)
            layout.addWidget(label, row, column * 2 + 1)

        # Space the columns evenly
        for column in range(columns):
            layout.setColumnStretch(column * 2 + 1, 1)

        group = QtWidgets.QGroupBox(self.tr("Key"))
        group.setLayout(layout)
        return group

    def controlsGroup(self):
        """
        Group box explaining how to use the map
        """
        controls = [
            (self.tr("Click"), self.tr("Select a planet")),
            (self.tr("Double-click"), self.tr("Travel to a planet")),
            (self.tr("Scroll"), self.tr("Zoom in and out")),
            (self.tr("Drag"), self.tr("Move the map")),
        ]

        layout = QtWidgets.QFormLayout()
        self.controlLabels = []
        for action, description in controls:
            actionLabel = QtWidgets.QLabel(action)
            font = actionLabel.font()
            font.setBold(True)
            actionLabel.setFont(font)
            descriptionLabel = QtWidgets.QLabel(description)
            self.controlLabels.append((actionLabel, descriptionLabel))
            layout.addRow(actionLabel, descriptionLabel)

        group = QtWidgets.QGroupBox(self.tr("Controls"))
        group.setLayout(layout)
        return group

    def build(self):
        """
        (Re)draw every planet, e.g. after travelling
        """
        state = self.parent.state
        self.scene.clear()
        self.hovered = None
        self.hoverLabel = None

        # Faint circles for the starting area, and for the current scout range
        radii = [const.INITIAL_GALAXY_RADIUS]
        if state.scout_level > 0:
            radii.append(state.discovery_distances()[1])

        pen = QtGui.QPen(RANGE_COLOR, 0, QtCore.Qt.DashLine)
        for radius in radii:
            r = radius * PIXELS_PER_LY
            self.scene.addEllipse(-r, -r, r * 2, r * 2, pen)

        search = self.parent.locationBrowser.planetSearchText.text().strip()
        self.matching = set(map(id, self.parent.locationBrowser.filteredPlanets())) if search else None

        self.layer = PlanetsLayer(self)
        self.scene.addItem(self.layer)

        # Grid of planets, for finding the planet under the mouse quickly
        self.grid = {}
        for planet in state.planets:
            self.grid.setdefault(self.gridCell(planet.x, planet.y), []).append(planet)

        # The current planet's name is always shown
        self.currentLabel = self.nameLabel(state.current_planet)

    def gridCell(self, x, y):
        return (int(math.floor(x / GRID_CELL_LY)), int(math.floor(y / GRID_CELL_LY)))

    def planetNear(self, pos, radius):
        """
        The planet nearest to 'pos' (in scene coordinates), if it's within 'radius'
        """
        x, y = pos.x() / PIXELS_PER_LY, -pos.y() / PIXELS_PER_LY
        r = radius / PIXELS_PER_LY
        low_x, low_y = self.gridCell(x - r, y - r)
        high_x, high_y = self.gridCell(x + r, y + r)

        nearest = None
        nearest_distance = r * r
        for cell_x in range(low_x, high_x + 1):
            for cell_y in range(low_y, high_y + 1):
                for planet in self.grid.get((cell_x, cell_y), ()):
                    distance = (planet.x - x) ** 2 + (planet.y - y) ** 2
                    if distance <= nearest_distance:
                        nearest = planet
                        nearest_distance = distance

        return nearest

    def isDimmed(self, planet):
        """
        True if the planets search box hides this planet
        """
        return (self.matching is not None) and (id(planet) not in self.matching)

    def specialPlanets(self):
        """
        Planets drawn differently from the ordinary grey dots, in drawing order
        """
        state = self.parent.state
        previous = [p for p in state.previous_planets if p in state.planets]
        ret = []
        for planet in previous[::-1] + [state.home_planet, self.selected, state.current_planet]:
            if (planet is not None) and (planet in state.planets) and not any(planet is p for p in ret):
                ret.append(planet)

        return ret

    def planetStyle(self, planet):
        """
        DotStyle for a planet
        """
        state = self.parent.state
        previous = [p for p in state.previous_planets if p in state.planets]

        style = DotStyle()
        if planet is state.current_planet:
            style.fill = CURRENT_COLOR
            style.size = CURRENT_DOT_SIZE
            style.outer_ring = CURRENT_COLOR
        elif planet in previous:
            style.fill = PREVIOUS_COLORS[previous.index(planet)]
        elif planet.visited:
            style.fill = VISITED_COLOR
        else:
            style.ring = UNVISITED_COLOR

        if planet is state.home_planet:
            style.ring = HOME_COLOR
            style.ring_width = 2.5
            style.size = max(style.size, LARGE_DOT_SIZE)

        if planet is self.selected:
            style.ring = SELECTED_COLOR
            style.ring_width = 2.5

        if self.isDimmed(planet):
            style.opacity = DIMMED_OPACITY

        return style

    def nameLabel(self, planet):
        """
        Show a planet's name next to it. It stays the same size when zooming
        """
        label = QtWidgets.QGraphicsSimpleTextItem(planet.full_name)
        label.setBrush(QtGui.QBrush(LABEL_COLOR))
        label.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations)
        label.setPos(scenePos(planet))
        label.setTransform(QtGui.QTransform.fromTranslate(CURRENT_RING_SIZE / 2.0, -CURRENT_RING_SIZE / 2.0 - 4))
        label.setZValue(10)
        self.scene.addItem(label)
        return label

    def tooltipText(self, planet):
        state = self.parent.state
        lines = [planet.full_name]
        if planet is state.current_planet:
            lines.append(self.tr("You are here"))
        else:
            lines.append(self.tr("{0} away, travel cost {1}", "{0} is a distance, e.g. 27.4 ly").format(
                         formatDistance(state.current_planet.distance_to(planet)),
                         formatNumber(state.travel_cost_to(planet))))

        if planet is state.home_planet:
            lines.append(self.tr("Home planet. Your warehouse is here."))

        return "<br>".join(lines)

    def fitToPlanets(self):
        """
        Zoom to show every planet
        """
        state = self.parent.state
        xs = [p.x for p in state.planets]
        ys = [p.y for p in state.planets]
        margin = 5.0
        rect = QtCore.QRectF((min(xs) - margin) * PIXELS_PER_LY, (-max(ys) - margin) * PIXELS_PER_LY,
                             (max(xs) - min(xs) + margin * 2) * PIXELS_PER_LY,
                             (max(ys) - min(ys) + margin * 2) * PIXELS_PER_LY)

        self.scene.setSceneRect(rect.adjusted(-rect.width(), -rect.height(), rect.width(), rect.height()))
        self.view.fitInView(rect, QtCore.Qt.KeepAspectRatio)

    def planetHovered(self, planet):
        """
        Show the name of the planet under the mouse (None if there isn't one)
        """
        if planet is self.hovered:
            return

        if self.hoverLabel is not None:
            self.scene.removeItem(self.hoverLabel)
            self.hoverLabel = None

        self.hovered = planet

        # The current planet's name is always shown already
        if (planet is not None) and (planet is not self.parent.state.current_planet):
            self.hoverLabel = self.nameLabel(planet)

    def planetClicked(self, planet):
        self.selected = planet
        self.layer.update()

        # Select the same planet in the planets table (unless the search box hides it)
        selectRowByKey(self.parent.locationBrowser.table, planet)

    def planetDoubleClicked(self, planet):
        self.parent.locationBrowser.travelToPlanet(planet)

        # The current planet, distances and costs may all have changed
        self.build()
