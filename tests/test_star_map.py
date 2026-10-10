import math
import time

import pytest
from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from deep_space_trader import star_map
from deep_space_trader import reputation
from deep_space_trader.star_map import StarMap, scenePos

from helpers import row_of


@pytest.fixture
def no_pirates(game, monkeypatch):
    monkeypatch.setattr(game.state, "pirate_chance", lambda planet: 0)


def spread_out(game):
    """
    Put the planets on a ring around the home planet, far enough apart that
    the mouse never picks a neighbouring planet by mistake (with clustering,
    planets can be close enough that their dots overlap)
    """
    state = game.state
    home = state.home_planet
    others = [p for p in state.planets if p is not home]
    for i, planet in enumerate(others):
        angle = 2 * math.pi * i / len(others)
        planet.x = home.x + 100.0 * math.cos(angle)
        planet.y = home.y + 100.0 * math.sin(angle)

    game.locationBrowser.refreshDistances()


@pytest.fixture
def starmap(game):
    spread_out(game)
    dialog = StarMap(game)
    dialog.resize(800, 650)
    dialog.show()
    QtWidgets.QApplication.processEvents()
    return dialog


def dot_pos(starmap, planet):
    """
    Position of a planet's dot in the map view, for clicking
    """
    return starmap.view.mapFromScene(scenePos(planet))


def move_mouse(starmap, pos):
    event = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, QtCore.QPointF(pos), QtCore.Qt.NoButton,
                              QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
    QtWidgets.QApplication.sendEvent(starmap.view.viewport(), event)


def drawn_planet_count(layer):
    """
    Number of planets the layer draws as ordinary dots
    """
    total = 0
    for group in layer.groups.values():
        total += len(group[-1])     # the opacities, one per planet
    return total


def test_every_planet_is_drawn_once(game, starmap):
    assert drawn_planet_count(starmap.layer) == len(game.state.planets)


def test_dot_styles(game, starmap, no_pirates):
    state = game.state
    home = state.home_planet
    target = state.planets[3]
    game.locationBrowser.travelToPlanet(target)
    starmap.build()

    current = starmap.planetStyle(target)
    assert current.fill == star_map.CURRENT_COLOR
    assert current.size == star_map.CURRENT_DOT_SIZE
    assert current.outer_ring == star_map.CURRENT_COLOR

    # Home is also the previous planet here: green fill, blue ring
    assert starmap.planetStyle(home).ring == star_map.HOME_COLOR
    assert starmap.planetStyle(home).fill == star_map.PREVIOUS_COLORS[0]

    unvisited = starmap.planetStyle(next(p for p in state.planets if not p.visited))
    assert unvisited.fill is None
    assert unvisited.ring == star_map.UNVISITED_COLOR

    # The few planets drawn on top of the ordinary dots
    assert set(map(id, starmap.specialPlanets())) == {id(target), id(home)}


def test_current_planet_stands_out(game, starmap):
    state = game.state
    current = starmap.planetStyle(state.current_planet)
    assert current.fill == star_map.CURRENT_COLOR
    assert current.fill not in star_map.PREVIOUS_COLORS
    assert current.size == star_map.CURRENT_DOT_SIZE
    # Its name is always shown, and it's drawn last, on top of everything else
    assert starmap.currentLabel.text() == state.current_planet.full_name
    assert starmap.specialPlanets()[-1] is state.current_planet


def test_tooltips(game, starmap):
    state = game.state
    other = state.planets[2]
    assert starmap.tooltipText(state.home_planet) == ("%s<br>You are here<br>Home planet. Your warehouse is here."
                                                      "<br>Reputation: Friendly (70)" % state.home_planet.full_name)
    assert starmap.tooltipText(other) == "%s<br>%.1f ly away, travel cost %s<br>Reputation: Friendly (70)" % (
        other.full_name, state.home_planet.distance_to(other), "{:,}".format(state.travel_cost_to(other)))


def test_tooltip_shown_near_a_dot(game, starmap):
    target = game.state.planets[3]
    pos = dot_pos(starmap, target) + QtCore.QPoint(star_map.PICK_RADIUS - 3, 0)
    event = QtGui.QHelpEvent(QtCore.QEvent.ToolTip, pos, starmap.view.viewport().mapToGlobal(pos))
    starmap.view.viewportEvent(event)
    assert QtWidgets.QToolTip.text() == starmap.tooltipText(target)


def test_hovering_shows_planet_name(game, starmap):
    target = game.state.planets[3]
    # Near the dot, not exactly on it
    move_mouse(starmap, dot_pos(starmap, target) + QtCore.QPoint(star_map.PICK_RADIUS - 3, 0))
    assert starmap.hovered is target
    assert starmap.hoverLabel.text() == target.full_name

    # Moving away removes the name
    move_mouse(starmap, QtCore.QPoint(2, 2))
    assert starmap.hovered is None
    assert starmap.hoverLabel is None


def test_click_selects_planet_in_table(game, starmap):
    target = game.state.planets[4]
    QtTest.QTest.mouseClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=dot_pos(starmap, target))
    assert starmap.selected is target
    assert starmap.planetStyle(target).ring == star_map.SELECTED_COLOR
    assert game.locationBrowser.selectedPlanet() is target

    # Selecting another planet clears the first one's outline
    other = game.state.planets[5]
    QtTest.QTest.mouseClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=dot_pos(starmap, other))
    assert starmap.planetStyle(target).ring != star_map.SELECTED_COLOR
    assert game.locationBrowser.selectedPlanet() is other


def test_click_near_a_dot_selects_it(game, starmap):
    target = game.state.planets[4]
    pos = dot_pos(starmap, target) + QtCore.QPoint(0, star_map.PICK_RADIUS - 3)
    QtTest.QTest.mouseClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=pos)
    assert starmap.selected is target


def test_nearest_planet_is_picked(game, starmap):
    a, b = game.state.planets[1:3]
    a.x, a.y = 100.0, 100.0
    b.x, b.y = 101.0, 100.0
    starmap.build()
    radius = 5 * star_map.PIXELS_PER_LY
    assert starmap.planetNear(QtCore.QPointF(1008, -1000), radius) is b
    assert starmap.planetNear(QtCore.QPointF(999, -1000), radius) is a
    assert starmap.planetNear(QtCore.QPointF(2000, 2000), radius) is None


def test_double_click_travels(game, dialogs, starmap, no_pirates):
    target = game.state.planets[4]
    QtTest.QTest.mouseDClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=dot_pos(starmap, target))
    assert dialogs.titles("question") == ["Travel"]
    assert game.state.current_planet is target
    assert starmap.planetStyle(target).fill == star_map.CURRENT_COLOR
    assert starmap.currentLabel.text() == target.full_name


def test_clicking_empty_space_does_nothing(game, starmap):
    selected = starmap.selected
    QtTest.QTest.mouseClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=QtCore.QPoint(2, 2))
    assert starmap.selected is selected


def test_zoom(starmap):
    scale = starmap.view.transform().m11()
    starmap.view.wheelEvent(type("Wheel", (), {"angleDelta": lambda self: QtCore.QPoint(0, 120)})())
    assert starmap.view.transform().m11() == pytest.approx(scale * star_map.ZOOM_STEP)


def test_search_dims_other_planets(game):
    target = game.state.planets[-1]
    QtTest.QTest.keyClicks(game.locationBrowser.planetSearchText, target.full_name)
    dialog = StarMap(game)
    for planet in game.state.planets:
        expected = 1.0 if planet is target else star_map.DIMMED_OPACITY
        assert dialog.planetStyle(planet).opacity == pytest.approx(expected)

    opacities = sorted(o for group in dialog.layer.groups.values() for o in group[-1])
    assert opacities == [star_map.DIMMED_OPACITY] * (len(game.state.planets) - 1) + [1.0]


def test_scout_range_circle(game):
    game.state.scout_level = 3
    dialog = StarMap(game)
    circles = [i for i in dialog.scene.items() if isinstance(i, QtWidgets.QGraphicsEllipseItem)]
    radii = sorted(c.rect().width() / 2 / star_map.PIXELS_PER_LY for c in circles)
    assert radii == [30.0, 120.0]


def test_opens_from_menu_and_button(game, dialogs):
    game.main.starMapAction.trigger()
    game.locationBrowser.starMapButton.click()
    assert [type(d) for d in dialogs.executed] == [StarMap, StarMap]


def test_selected_table_row_is_selected_on_map(game):
    target = game.state.planets[2]
    table = game.locationBrowser.table
    table.setCurrentCell(row_of(table, target), 0)
    assert StarMap(game).selected is target


def test_draws_without_the_fast_path(game, monkeypatch):
    # If pyqtgraph's helper for drawing many dots at once isn't available
    monkeypatch.setattr(star_map, "PrimitiveArray", None)
    dialog = StarMap(game)
    dialog.resize(800, 650)
    dialog.show()
    dialog.view.viewport().repaint()
    assert drawn_planet_count(dialog.layer) == len(game.state.planets)


@pytest.fixture
def big_galaxy(game):
    game.state.scout_level = 10
    game.state.expand_planets(20000 - len(game.state.planets))
    return game


def test_builds_quickly_with_many_planets(big_galaxy):
    start = time.time()
    dialog = StarMap(big_galaxy)
    assert drawn_planet_count(dialog.layer) == 20000
    assert time.time() - start < 5


@pytest.mark.parametrize("fast", [True, False])
def test_zooms_quickly_with_many_planets(big_galaxy, monkeypatch, fast):
    # Each zoom step used to take about 250 ms to draw with 20,000 planets
    if not fast:
        monkeypatch.setattr(star_map, "PrimitiveArray", None)

    dialog = StarMap(big_galaxy)
    dialog.resize(1000, 800)
    dialog.show()
    view = dialog.view
    view.viewport().repaint()

    times = []
    for _ in range(3):
        view.scale(star_map.ZOOM_STEP, star_map.ZOOM_STEP)
        start = time.time()
        view.viewport().repaint()
        times.append(time.time() - start)

    # Generous limits, for slower machines: drawing used to take about 0.25 s on
    # a fast machine, and the fast path now takes about 0.01 s
    assert min(times) < (0.1 if fast else 0.5)


def test_legend(starmap):
    groups = {g.title(): g for g in starmap.findChildren(QtWidgets.QGroupBox)}
    assert set(groups) == {"Key", "Controls"}

    assert [label.text() for label in starmap.keyLabels] == [
        "You are here", "Previous planets", "Home planet", "Visited", "Not visited", "Selected"]
    icons = [w for w in groups["Key"].findChildren(QtWidgets.QLabel)
             if w.pixmap() is not None and not w.pixmap().isNull() and w not in starmap.reputationKeyWidgets]
    assert len(icons) == 6

    assert [(a.text(), d.text()) for a, d in starmap.controlLabels] == [
        ("Click", "Select a planet"), ("Double-click", "Travel to a planet"),
        ("Scroll", "Zoom in and out"), ("Drag", "Move the map"),
        ("Enter", "Item prices on the selected planet")]


def journey_points(starmap):
    path = starmap.journeyLine.path()
    return [(round(path.elementAt(i).x, 3), round(path.elementAt(i).y, 3)) for i in range(path.elementCount())]


def expected_points(planets):
    return [(round(scenePos(p).x(), 3), round(scenePos(p).y(), 3)) for p in planets]


def test_journey_line(game, no_pirates):
    state = game.state
    for planet in (state.planets[3], state.planets[5], state.home_planet):
        game.locationBrowser.travelToPlanet(planet)

    dialog = StarMap(game)
    assert journey_points(dialog) == expected_points(state.journey)
    assert len(state.journey) == 4
    assert dialog.journeyLine.pen().color() == star_map.JOURNEY_COLOR
    # Drawn under the planets
    assert dialog.journeyLine.zValue() < dialog.layer.zValue()


def test_journey_line_grows_when_travelling_from_the_map(game, dialogs, starmap, no_pirates):
    # No line until the first trip
    assert journey_points(starmap) == []
    target = game.state.planets[4]
    QtTest.QTest.mouseDClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=dot_pos(starmap, target))
    assert journey_points(starmap) == expected_points([game.state.home_planet, target])


def test_enter_opens_trading_console_for_selected_planet(game, dialogs, starmap):
    from deep_space_trader.location_browser import TradingConsole
    game.state.enable_trading_console()
    target = game.state.planets[4]
    QtTest.QTest.mouseClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=dot_pos(starmap, target))
    QtTest.QTest.keyClick(starmap.view, QtCore.Qt.Key_Return)
    assert [type(d) for d in dialogs.executed] == [TradingConsole]
    assert dialogs.executed[0].windowTitle() == "Item prices on %s" % target.full_name


def test_enter_without_trading_console(game, dialogs, starmap):
    target = game.state.planets[4]
    QtTest.QTest.mouseClick(starmap.view.viewport(), QtCore.Qt.LeftButton, pos=dot_pos(starmap, target))
    QtTest.QTest.keyClick(starmap.view, QtCore.Qt.Key_Enter)
    assert dialogs.executed == []
    assert len(dialogs.messages("error")) == 1
    assert "trading console" in dialogs.messages("error")[0]


def test_enter_with_no_planet_selected(game, dialogs):
    game.state.enable_trading_console()
    game.locationBrowser.table.setCurrentCell(-1, -1)
    dialog = StarMap(game)
    dialog.show()
    QtTest.QTest.keyClick(dialog.view, QtCore.Qt.Key_Return)
    assert dialogs.executed == []
    assert dialogs.shown == []


# ----- Reputation -----

def ordinary_planet(game, starmap):
    """
    A planet drawn as an ordinary dot (not current, home, previous or selected)
    """
    return next(p for p in game.state.planets if p not in starmap.specialPlanets())


def dot_color(starmap, planet):
    starmap.layer.update()
    image = starmap.view.viewport().grab().toImage()
    pos = dot_pos(starmap, planet) * starmap.view.devicePixelRatioF()
    return image.pixelColor(pos.x(), pos.y()).name()


def open_map(game):
    spread_out(game)
    dialog = StarMap(game)
    dialog.resize(800, 650)
    dialog.show()
    QtWidgets.QApplication.processEvents()
    return dialog


def test_tooltip_shows_reputation(game, starmap):
    planet = game.state.planets[2]
    game.state.planets_destroyed([planet])
    value = game.state.reputation_of(planet)
    assert starmap.tooltipText(planet).endswith("<br>Reputation: %s (%d)" % (reputation.levelName(value), round(value)))


def test_colour_by_reputation(game):
    state = game.state
    starmap = open_map(game)
    planet = ordinary_planet(game, starmap)
    planet.visited = True
    state.planets_destroyed([planet])
    state.planets_destroyed([planet])
    level = reputation.level(state.reputation_of(planet))
    assert level >= reputation.HOSTILE

    starmap = open_map(game)
    assert not starmap.reputationCheckBox.isChecked()
    assert dot_color(starmap, planet) == star_map.VISITED_COLOR.name()
    assert not any(w.isVisible() for w in starmap.reputationKeyWidgets)

    starmap.reputationCheckBox.setChecked(True)
    assert dot_color(starmap, planet) == reputation.LEVEL_COLORS[level]
    assert all(w.isVisible() for w in starmap.reputationKeyWidgets)
    labels = [w.text() for w in starmap.reputationKeyWidgets if not w.text() == ""]
    assert labels == ["Allied", "Friendly", "Wary", "Hostile", "Refuses to trade"]


def test_colour_by_reputation_is_kept_while_the_game_is_open(game):
    open_map(game).reputationCheckBox.setChecked(True)
    assert open_map(game).reputationCheckBox.isChecked()

    # A new game in the same window keeps it too; only restarting the game resets it
    game.reset()
    assert open_map(game).reputationCheckBox.isChecked()


def test_colour_by_reputation_is_not_saved(game, monkeypatch):
    from deep_space_trader import config
    open_map(game).reputationCheckBox.setChecked(True)
    assert all(not isinstance(v, bool) or k == config.SHOWINTRO_KEY for k, v in config.config.items())


def test_colours_follow_travel(game, no_pirates):
    state = game.state
    starmap = open_map(game)
    starmap.reputationCheckBox.setChecked(True)
    victim = ordinary_planet(game, starmap)
    state.planets_destroyed([victim, victim, victim])
    starmap.planetDoubleClicked(victim)
    assert state.current_planet is victim
    levels = {key[1] for key in starmap.layer.groups}
    assert levels == {reputation.level(v) for v in state.reputations(state.planets)}


@pytest.mark.parametrize("fast", [True, False])
def test_colouring_by_reputation_is_fast_with_many_planets(big_galaxy, monkeypatch, fast):
    if not fast:
        monkeypatch.setattr(star_map, "PrimitiveArray", None)

    state = big_galaxy.state
    state.planets_destroyed(state.planets[1::3])

    start = time.time()
    dialog = StarMap(big_galaxy)
    assert time.time() - start < 5
    assert drawn_planet_count(dialog.layer) == 20000

    dialog.resize(1000, 800)
    dialog.show()
    dialog.reputationCheckBox.setChecked(True)
    view = dialog.view
    view.viewport().repaint()

    times = []
    for _ in range(3):
        view.scale(star_map.ZOOM_STEP, star_map.ZOOM_STEP)
        start = time.time()
        view.viewport().repaint()
        times.append(time.time() - start)

    assert min(times) < (0.1 if fast else 0.5)
