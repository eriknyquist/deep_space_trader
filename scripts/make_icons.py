"""
Make the game's icons: those shown in message boxes about special events
(pirates, customs patrols, black markets), next to the current planet's
picture (home), and on the main window's buttons, and save them as PNG files
in deep_space_trader/images.

The game loads these files (see deep_space_trader/icons.py); this script is
only needed to change them. Each icon is drawn on a 100x100 grid and saved at
256x256 pixels, which the game scales down to the size it shows them at.
They can also be edited, or replaced, in any image editor.

Usage (from the project folder):

    python scripts/make_icons.py                   # all icons, saved in deep_space_trader/images
    python scripts/make_icons.py --output preview  # save them somewhere else
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PyQt5 import QtCore, QtGui  # noqa: E402

from deep_space_trader import icons  # noqa: E402
from deep_space_trader.utils import IMAGE_DIR  # noqa: E402


OUTLINE = QtGui.QColor("#1a1a1a")

def _pen(width, color=OUTLINE):
    pen = QtGui.QPen(color, width)
    pen.setJoinStyle(QtCore.Qt.RoundJoin)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    return pen


# Crossbones: where they cross, their angles from horizontal (in degrees), and
# their shape (half the length of the shaft, its width, and the size of the
# two round bulbs at each end)
BONES_CENTRE = QtCore.QPointF(50, 64)
BONE_ANGLES = (32, -32)
BONE_HALF_LENGTH = 33
BONE_WIDTH = 9
BONE_BULB_RADIUS = 6.5
BONE_BULB_SPREAD = 5


def bonePath(angle):
    """
    One bone, as a single outline: drawn lying along the x axis, with the
    bulbs on either side of each end (across the shaft), then turned to 'angle'
    and moved to BONES_CENTRE
    """
    path = QtGui.QPainterPath()
    path.addRect(QtCore.QRectF(-BONE_HALF_LENGTH, -BONE_WIDTH / 2.0, BONE_HALF_LENGTH * 2, BONE_WIDTH))
    for x in (-BONE_HALF_LENGTH, BONE_HALF_LENGTH):
        for y in (-BONE_BULB_SPREAD, BONE_BULB_SPREAD):
            bulb = QtGui.QPainterPath()
            bulb.addEllipse(QtCore.QPointF(x, y), BONE_BULB_RADIUS, BONE_BULB_RADIUS)
            path = path.united(bulb)

    transform = QtGui.QTransform()
    transform.translate(BONES_CENTRE.x(), BONES_CENTRE.y())
    transform.rotate(angle)
    return transform.map(path)


def _drawPirates(painter):
    """
    Skull and crossbones
    """
    bone = QtGui.QColor("#ece6d6")

    # Crossbones, behind the skull
    for angle in BONE_ANGLES:
        painter.setPen(_pen(3))
        painter.setBrush(bone)
        painter.drawPath(bonePath(angle))

    # Skull: a round head and a jaw
    painter.setPen(_pen(3))
    painter.setBrush(bone)
    head = QtGui.QPainterPath()
    head.addEllipse(QtCore.QRectF(24, 8, 52, 50))
    jaw = QtGui.QPainterPath()
    jaw.addRoundedRect(QtCore.QRectF(35, 46, 30, 22), 6, 6)
    painter.drawPath(head.united(jaw))

    # Eyes, nose and teeth
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(OUTLINE)
    painter.drawEllipse(QtCore.QRectF(32, 27, 14, 14))
    painter.drawEllipse(QtCore.QRectF(54, 27, 14, 14))
    painter.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(50, 43), QtCore.QPointF(45, 52), QtCore.QPointF(55, 52)]))
    painter.setPen(_pen(2))
    for x in (43, 50, 57):
        painter.drawLine(QtCore.QPointF(x, 58), QtCore.QPointF(x, 67))


def _drawCustoms(painter):
    """
    A police-style shield, with a star
    """
    shield = QtGui.QPainterPath()
    shield.moveTo(50, 6)
    shield.cubicTo(66, 14, 78, 15, 88, 14)
    shield.cubicTo(90, 52, 78, 78, 50, 94)
    shield.cubicTo(22, 78, 10, 52, 12, 14)
    shield.cubicTo(22, 15, 34, 14, 50, 6)
    shield.closeSubpath()

    painter.setPen(_pen(7, QtGui.QColor("#d9a520")))
    painter.setBrush(QtGui.QColor("#2b5fb4"))
    painter.drawPath(shield)

    # Five-pointed star in the middle
    points = []
    for i in range(10):
        r = 24 if i % 2 == 0 else 10
        angle = math.radians(-90 + i * 36)
        points.append(QtCore.QPointF(50 + r * math.cos(angle), 49 + r * math.sin(angle)))

    painter.setPen(_pen(2.5, QtGui.QColor("#8a6510")))
    painter.setBrush(QtGui.QColor("#f2c94c"))
    painter.drawPolygon(QtGui.QPolygonF(points))


def _drawBlackMarket(painter):
    """
    A wooden crate, with a red X painted on it
    """
    wood = QtGui.QColor("#a8743f")
    dark = QtGui.QColor("#5c3a1a")

    painter.setPen(_pen(4, dark))
    painter.setBrush(wood)
    painter.drawRect(QtCore.QRectF(12, 14, 76, 74))

    # Planks, and a frame around the front
    painter.setPen(_pen(2, dark))
    for y in (32.5, 51, 69.5):
        painter.drawLine(QtCore.QPointF(14, y), QtCore.QPointF(86, y))
    painter.setPen(_pen(7, dark))
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawRect(QtCore.QRectF(17, 19, 66, 64))

    # The X, a little see-through, so the planks show through the paint. The two
    # strokes are merged into one shape first, so where they cross isn't painted
    # twice (which would make the middle darker)
    x = QtGui.QPainterPath()
    centre, reach = QtCore.QPointF(50, 51), 22
    for dx, dy in ((1, 1), (1, -1)):
        x.moveTo(centre.x() - dx * reach, centre.y() - dy * reach)
        x.lineTo(centre.x() + dx * reach, centre.y() + dy * reach)

    stroker = QtGui.QPainterPathStroker()
    stroker.setWidth(11)
    stroker.setCapStyle(QtCore.Qt.FlatCap)
    painter.setOpacity(0.75)
    painter.fillPath(stroker.createStroke(x).simplified(), QtGui.QColor("#d32f2f"))
    painter.setOpacity(1.0)


def _drawHome(painter):
    """
    A little house, with a chimney, a door and two windows
    """
    walls = QtGui.QColor("#eadfc8")
    roof = QtGui.QColor("#c0504d")
    wood = QtGui.QColor("#7a4a2a")
    glass = QtGui.QColor("#9fd3f0")

    # Chimney, behind the roof
    painter.setPen(_pen(3.5))
    painter.setBrush(roof.darker(115))
    painter.drawRect(QtCore.QRectF(64, 16, 11, 26))

    # Walls
    painter.setBrush(walls)
    painter.drawRect(QtCore.QRectF(20, 46, 60, 44))

    # Roof, overhanging the walls
    painter.setBrush(roof)
    painter.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(8, 52), QtCore.QPointF(50, 12),
                                         QtCore.QPointF(92, 52)]))

    # Door, with a rounded top and a knob
    painter.setPen(_pen(3))
    painter.setBrush(wood)
    door = QtGui.QPainterPath()
    door.addRoundedRect(QtCore.QRectF(42, 62, 16, 30), 7, 7)
    clip = QtGui.QPainterPath()
    clip.addRect(QtCore.QRectF(0, 0, 100, 90))
    painter.drawPath(door.intersected(clip))
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(QtGui.QColor("#e8c25a"))
    painter.drawEllipse(QtCore.QPointF(54, 77), 1.8, 1.8)

    # Windows, with crossed frames
    for x in (26, 63):
        painter.setPen(_pen(3))
        painter.setBrush(glass)
        painter.drawRect(QtCore.QRectF(x, 58, 12, 12))
        painter.setPen(_pen(2))
        painter.drawLine(QtCore.QPointF(x + 6, 58), QtCore.QPointF(x + 6, 70))
        painter.drawLine(QtCore.QPointF(x, 64), QtCore.QPointF(x + 12, 64))


# ----- Button icons -----
#
# Simple line drawings, in white on a see-through background: the game tints
# them to the colour of the button text (see icons.buttonIcon), so they suit
# the dark and light themes, and look greyed out on disabled buttons

LINE = QtGui.QColor("#ffffff")


def _line(painter, width=7):
    painter.setPen(_pen(width, LINE))
    painter.setBrush(QtCore.Qt.NoBrush)


def _arrow(painter, start, end, head=14):
    """
    A straight arrow from 'start' to 'end' (points), with an open head at 'end'
    """
    painter.drawLine(start, end)
    angle = math.atan2(end.y() - start.y(), end.x() - start.x())
    for side in (-1, 1):
        a = angle + math.pi + side * math.radians(40)
        painter.drawLine(end, QtCore.QPointF(end.x() + head * math.cos(a), end.y() + head * math.sin(a)))


def P(x, y):
    return QtCore.QPointF(x, y)


def _drawStore(painter):
    """
    A shop front, with a striped awning
    """
    _line(painter)
    painter.drawPolyline(QtGui.QPolygonF([P(14, 30), P(22, 12), P(78, 12), P(86, 30)]))
    awning = QtGui.QPainterPath(P(14, 30))
    for i in range(4):
        x = 14 + i * 18
        awning.arcTo(QtCore.QRectF(x, 21, 18, 18), 180, 180)
    painter.drawPath(awning)
    painter.drawLine(P(14, 30), P(86, 30))
    painter.drawPolyline(QtGui.QPolygonF([P(20, 40), P(20, 88), P(80, 88), P(80, 40)]))
    painter.drawRect(QtCore.QRectF(30, 56, 20, 32))
    painter.drawRect(QtCore.QRectF(58, 52, 14, 14))


def _drawNextDay(painter):
    """
    A calendar page, with an arrow to the next day
    """
    _line(painter)
    painter.drawRoundedRect(QtCore.QRectF(12, 18, 76, 70), 8, 8)
    painter.drawLine(P(12, 36), P(88, 36))
    painter.drawLine(P(32, 8), P(32, 26))
    painter.drawLine(P(68, 8), P(68, 26))
    _arrow(painter, P(30, 62), P(70, 62), head=13)


def _drawReset(painter):
    """
    A circular arrow: start again
    """
    _line(painter)

    # Most of a circle, from 120 degrees round (anticlockwise) to 60, with the
    # arrowhead at the end, pointing on round the circle
    painter.drawArc(QtCore.QRectF(16, 16, 68, 68), 120 * 16, 300 * 16)
    end = math.radians(60)
    tip = P(50 + 34 * math.cos(end), 50 - 34 * math.sin(end))
    along = math.atan2(-math.cos(end), -math.sin(end))
    for side in (-1, 1):
        back = along + math.pi + side * math.radians(40)
        painter.drawLine(tip, P(tip.x() + 16 * math.cos(back), tip.y() + 16 * math.sin(back)))


def _drawTravel(painter):
    """
    A rocket, flying up and to the right
    """
    _line(painter, 6)
    painter.save()
    painter.translate(50, 50)
    painter.rotate(45)
    body = QtGui.QPainterPath(P(0, -44))
    body.cubicTo(P(16, -30), P(16, 6), P(12, 18))
    body.lineTo(P(-12, 18))
    body.cubicTo(P(-16, 6), P(-16, -30), P(0, -44))
    painter.drawPath(body)
    painter.drawEllipse(P(0, -14), 6, 6)
    painter.drawPolyline(QtGui.QPolygonF([P(12, 2), P(24, 14), P(22, 30), P(12, 18)]))
    painter.drawPolyline(QtGui.QPolygonF([P(-12, 2), P(-24, 14), P(-22, 30), P(-12, 18)]))
    painter.drawLine(P(-6, 26), P(-6, 38))
    painter.drawLine(P(6, 26), P(6, 38))
    painter.restore()


def _drawTravelPrevious(painter):
    """
    A U-turn arrow: back where you came from
    """
    _line(painter)
    path = QtGui.QPainterPath(P(78, 84))
    path.lineTo(P(78, 46))
    path.arcTo(QtCore.QRectF(28, 22, 50, 48), 0, 180)
    path.lineTo(P(28, 58))
    painter.drawPath(path)
    painter.drawLine(P(28, 60), P(14, 44))
    painter.drawLine(P(28, 60), P(42, 44))


def _drawTravelHome(painter):
    """
    A house
    """
    _line(painter)
    painter.drawPolyline(QtGui.QPolygonF([P(10, 48), P(50, 12), P(90, 48)]))
    painter.drawPolyline(QtGui.QPolygonF([P(22, 38), P(22, 88), P(78, 88), P(78, 38)]))
    painter.drawPolyline(QtGui.QPolygonF([P(42, 88), P(42, 62), P(58, 62), P(58, 88)]))


def _drawTradingConsole(painter):
    """
    A screen with a price chart on it
    """
    _line(painter)
    painter.drawRoundedRect(QtCore.QRectF(8, 12, 84, 58), 6, 6)
    painter.drawLine(P(50, 70), P(50, 84))
    painter.drawLine(P(30, 86), P(70, 86))
    painter.drawPolyline(QtGui.QPolygonF([P(20, 56), P(36, 40), P(50, 50), P(64, 30), P(80, 38)]))


def _drawStarMap(painter):
    """
    A constellation: stars joined by lines
    """
    stars = [P(16, 70), P(36, 30), P(60, 52), P(84, 18), P(76, 84)]
    _line(painter, 4)
    painter.drawPolyline(QtGui.QPolygonF(stars[:4]))
    painter.drawLine(stars[2], stars[4])
    painter.setPen(_pen(4, LINE))
    painter.setBrush(QtCore.Qt.NoBrush)
    for star in stars:
        painter.drawEllipse(star, 8, 8)


def _drawBuy(painter):
    """
    A shopping trolley
    """
    _line(painter)
    painter.drawPolyline(QtGui.QPolygonF([P(6, 16), P(20, 16), P(32, 66), P(80, 66)]))
    painter.drawPolyline(QtGui.QPolygonF([P(24, 30), P(90, 30), P(82, 54), P(29, 54)]))
    painter.drawEllipse(P(38, 82), 7, 7)
    painter.drawEllipse(P(74, 82), 7, 7)


def _tag(painter, dx=0, dy=0):
    tag = QtGui.QPolygonF([P(14 + dx, 14 + dy), P(52 + dx, 14 + dy), P(88 + dx, 50 + dy),
                           P(50 + dx, 88 + dy), P(14 + dx, 52 + dy)])
    painter.drawPolygon(tag)
    painter.drawEllipse(P(32 + dx, 32 + dy), 6, 6)


def _drawSell(painter):
    """
    A price tag
    """
    _line(painter)
    _tag(painter)


def _drawSellAll(painter):
    """
    Two price tags
    """
    _line(painter, 6)
    painter.save()
    painter.translate(8, 6)
    painter.scale(0.85, 0.85)
    _tag(painter, 14, -6)
    painter.restore()
    painter.save()
    painter.translate(-2, 16)
    painter.scale(0.85, 0.85)
    # (the front tag hides the back tag where they overlap)
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(QtGui.QColor(0, 0, 0))
    painter.drawPolygon(QtGui.QPolygonF([P(14, 14), P(52, 14), P(88, 50), P(50, 88), P(14, 52)]))
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
    _line(painter, 6 / 0.85)
    _tag(painter)
    painter.restore()


def _warehouse(painter):
    """
    A wide building with a big door (the warehouse)
    """
    painter.drawPolyline(QtGui.QPolygonF([P(8, 40), P(50, 16), P(92, 40)]))
    painter.drawPolyline(QtGui.QPolygonF([P(16, 36), P(16, 88), P(84, 88), P(84, 36)]))
    painter.drawRect(QtCore.QRectF(34, 58, 32, 30))


def _drawToWarehouse(painter):
    """
    The warehouse, with an arrow going in
    """
    _line(painter)
    _warehouse(painter)
    _arrow(painter, P(50, 2), P(50, 46), head=12)


def _drawRetrieve(painter):
    """
    The warehouse, with an arrow coming out
    """
    _line(painter)
    _warehouse(painter)
    _arrow(painter, P(50, 50), P(50, 4), head=12)


def _drawRetrieveAll(painter):
    """
    The warehouse, with two arrows coming out
    """
    _line(painter)
    _warehouse(painter)
    _arrow(painter, P(38, 50), P(38, 4), head=11)
    _arrow(painter, P(62, 50), P(62, 4), head=11)


def _bin(painter):
    painter.drawLine(P(14, 24), P(86, 24))
    painter.drawPolyline(QtGui.QPolygonF([P(38, 24), P(40, 12), P(60, 12), P(62, 24)]))
    painter.drawPolyline(QtGui.QPolygonF([P(22, 24), P(28, 90), P(72, 90), P(78, 24)]))


def _drawDump(painter):
    """
    A rubbish bin
    """
    _line(painter)
    _bin(painter)
    for x in (40, 60):
        painter.drawLine(P(x, 38), P(x, 76))


def _drawDumpAll(painter):
    """
    A rubbish bin with a cross on it: everything goes
    """
    _line(painter)
    _bin(painter)
    painter.drawLine(P(36, 40), P(64, 74))
    painter.drawLine(P(64, 40), P(36, 74))


# Button icon name (see deep_space_trader/icons.py) -> function that draws it
BUTTON_DRAWERS = {
    icons.STORE: _drawStore,
    icons.NEXT_DAY: _drawNextDay,
    icons.RESET: _drawReset,
    icons.TRAVEL: _drawTravel,
    icons.TRAVEL_PREVIOUS: _drawTravelPrevious,
    icons.TRAVEL_HOME: _drawTravelHome,
    icons.TRADING_CONSOLE: _drawTradingConsole,
    icons.STAR_MAP: _drawStarMap,
    icons.BUY: _drawBuy,
    icons.SELL: _drawSell,
    icons.SELL_ALL: _drawSellAll,
    icons.TO_WAREHOUSE: _drawToWarehouse,
    icons.RETRIEVE: _drawRetrieve,
    icons.RETRIEVE_ALL: _drawRetrieveAll,
    icons.DUMP: _drawDump,
    icons.DUMP_ALL: _drawDumpAll,
}


# Icon name (see deep_space_trader/icons.py) -> function that draws it
DRAWERS = {
    icons.PIRATES: _drawPirates,
    icons.CUSTOMS: _drawCustoms,
    icons.BLACK_MARKET: _drawBlackMarket,
    icons.HOME: _drawHome,
}


ALL_DRAWERS = dict(DRAWERS, **BUTTON_DRAWERS)


def makeIcon(name, size=icons.FILE_SIZE):
    """
    The icon 'name' (e.g. icons.PIRATES), as a 'size' x 'size' image
    """
    image = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
    image.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.scale(size / 100.0, size / 100.0)
    ALL_DRAWERS[name](painter)
    painter.end()
    return image


def main(args=None):
    parser = argparse.ArgumentParser(description="Make the game's icons")
    parser.add_argument("--output", default=IMAGE_DIR,
                        help="folder to save the icons in (default: deep_space_trader/images)")
    args = parser.parse_args(args)

    # Drawing needs a QGuiApplication, which has to stay alive until the end
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication(sys.argv[:1])
    app.setApplicationName("make_icons")
    os.makedirs(args.output, exist_ok=True)
    for name in ALL_DRAWERS:
        path = os.path.join(args.output, icons.FILENAMES[name])
        makeIcon(name).save(path)
        print("saved %s" % path)


if __name__ == "__main__":
    main()
