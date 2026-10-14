"""
Make the icons shown in message boxes about special events (pirates, customs
patrols, black markets), and save them as PNG files in deep_space_trader/images.

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


# Icon name (see deep_space_trader/icons.py) -> function that draws it
DRAWERS = {
    icons.PIRATES: _drawPirates,
    icons.CUSTOMS: _drawCustoms,
    icons.BLACK_MARKET: _drawBlackMarket,
}


def makeIcon(name, size=icons.FILE_SIZE):
    """
    The icon 'name' (e.g. icons.PIRATES), as a 'size' x 'size' image
    """
    image = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
    image.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.scale(size / 100.0, size / 100.0)
    DRAWERS[name](painter)
    painter.end()
    return image


def main(args=None):
    parser = argparse.ArgumentParser(description="Make the message box icons")
    parser.add_argument("--output", default=IMAGE_DIR,
                        help="folder to save the icons in (default: deep_space_trader/images)")
    args = parser.parse_args(args)

    # Drawing needs a QGuiApplication, which has to stay alive until the end
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication(sys.argv[:1])
    app.setApplicationName("make_icons")
    os.makedirs(args.output, exist_ok=True)
    for name in DRAWERS:
        path = os.path.join(args.output, icons.FILENAMES[name])
        makeIcon(name).save(path)
        print("saved %s" % path)


if __name__ == "__main__":
    main()
