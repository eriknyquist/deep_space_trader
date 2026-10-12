"""
Icons for message boxes about special events (see utils.infoDialog and
utils.choiceDialog), drawn in code rather than loaded from image files.
Each is drawn on a 100x100 grid, and scaled to the size it's shown at
"""
import math

from PyQt5 import QtCore, QtGui

# Icon names, passed to the dialog functions
PIRATES = "pirates"
CUSTOMS = "customs"
BLACK_MARKET = "black_market"

OUTLINE = QtGui.QColor("#1a1a1a")

# (name, size, device pixel ratio) -> QPixmap
_cache = {}


def _pen(width, color=OUTLINE):
    pen = QtGui.QPen(color, width)
    pen.setJoinStyle(QtCore.Qt.RoundJoin)
    pen.setCapStyle(QtCore.Qt.RoundCap)
    return pen


def _drawPirates(painter):
    """
    Skull and crossbones
    """
    bone = QtGui.QColor("#ece6d6")

    # Crossbones, behind the skull: an outlined thick line with a knob at each end
    for (x1, y1, x2, y2) in ((18, 50, 82, 92), (82, 50, 18, 92)):
        for color, extra in ((OUTLINE, 5), (bone, 0)):
            painter.setPen(_pen(10 + extra, color))
            painter.drawLine(QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2))
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(color)
            for x, y in ((x1, y1), (x2, y2)):
                dx = -1 if x < 50 else 1
                for oy in (-5, 5):
                    r = 6.5 + extra / 2.0
                    painter.drawEllipse(QtCore.QPointF(x + dx * 2, y + oy * (1 if y < 70 else -1) * 0.8 + 0), r, r)

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
    A wooden crate, stamped with a red mark
    """
    wood = QtGui.QColor("#a8743f")
    dark = QtGui.QColor("#5c3a1a")

    painter.setPen(_pen(4, dark))
    painter.setBrush(wood)
    painter.drawRect(QtCore.QRectF(12, 18, 76, 70))

    # Planks, and a frame with a diagonal brace
    painter.setPen(_pen(2, dark))
    for y in (35.5, 53, 70.5):
        painter.drawLine(QtCore.QPointF(14, y), QtCore.QPointF(86, y))
    painter.setPen(_pen(7, dark))
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.drawRect(QtCore.QRectF(17, 23, 66, 60))
    painter.drawLine(QtCore.QPointF(20, 80), QtCore.QPointF(80, 26))
    painter.setPen(_pen(4, QtGui.QColor("#c48a50")))
    painter.drawLine(QtCore.QPointF(20, 80), QtCore.QPointF(80, 26))

    # The red ring that marks black markets on the star map
    painter.setPen(_pen(6, QtGui.QColor("#e53935")))
    painter.drawEllipse(QtCore.QPointF(72, 24), 15, 15)
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(QtGui.QColor("#e53935"))
    painter.drawEllipse(QtCore.QPointF(72, 24), 6, 6)


_drawers = {
    PIRATES: _drawPirates,
    CUSTOMS: _drawCustoms,
    BLACK_MARKET: _drawBlackMarket,
}


def iconPixmap(name, size, dpr=1.0):
    """
    The icon 'name' (e.g. PIRATES), 'size' pixels across. 'dpr' is the screen's
    device pixel ratio, so the icon is sharp on high-DPI screens
    """
    key = (name, size, dpr)
    if key not in _cache:
        pixmap = QtGui.QPixmap(int(math.ceil(size * dpr)), int(math.ceil(size * dpr)))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.scale(size / 100.0, size / 100.0)
        _drawers[name](painter)
        painter.end()
        _cache[key] = pixmap

    return _cache[key]
