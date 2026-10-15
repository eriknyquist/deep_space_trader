"""
Icons for message boxes about special events (see utils.setMessageBoxIcon),
for the current planet in the information section, and for the main window's
buttons (see setButtonIcon).
They're PNG files in the images folder, made by scripts/make_icons.py (which is
only needed to change them), and scaled down to the size they're shown at
"""
import math
import os

from PyQt5 import QtCore, QtGui, QtWidgets

# (utils imports this module, so IMAGE_DIR is looked up when it's needed, once utils is loaded)
from deep_space_trader import utils

# Icon names, passed to the dialog functions
PIRATES = "pirates"
CUSTOMS = "customs"
BLACK_MARKET = "black_market"
HOME = "home"

# Button icon names (see setButtonIcon)
STORE = "store"
NEXT_DAY = "next_day"
RESET = "reset"
TRAVEL = "travel"
TRAVEL_PREVIOUS = "travel_previous"
TRAVEL_HOME = "travel_home"
TRADING_CONSOLE = "trading_console"
STAR_MAP = "star_map"
BUY = "buy"
SELL = "sell"
SELL_ALL = "sell_all"
TO_WAREHOUSE = "to_warehouse"
RETRIEVE = "retrieve"
RETRIEVE_ALL = "retrieve_all"
DUMP = "dump"
DUMP_ALL = "dump_all"

BUTTON_ICONS = [STORE, NEXT_DAY, RESET, TRAVEL, TRAVEL_PREVIOUS, TRAVEL_HOME, TRADING_CONSOLE,
                STAR_MAP, BUY, SELL, SELL_ALL, TO_WAREHOUSE, RETRIEVE, RETRIEVE_ALL, DUMP, DUMP_ALL]

FILENAMES = {
    PIRATES: "event_pirates.png",
    CUSTOMS: "event_customs.png",
    BLACK_MARKET: "event_black_market.png",
    HOME: "home.png",
}
FILENAMES.update({name: "button_%s.png" % name for name in BUTTON_ICONS})

# Size of the files, in pixels: large enough to stay sharp at any size the
# icons are shown at, up to 4x scaling on high-DPI screens
FILE_SIZE = 256

# (name, size, device pixel ratio) -> QPixmap
_cache = {}


def iconPixmap(name, size, dpr=1.0):
    """
    The icon 'name' (e.g. PIRATES), 'size' pixels across. 'dpr' is the screen's
    device pixel ratio, so the icon is sharp on high-DPI screens
    """
    key = (name, size, dpr)
    if key not in _cache:
        pixels = int(round(size * dpr))

        # Scaled smoothly, once: scaling while drawing would make jagged edges
        pixmap = QtGui.QPixmap(os.path.join(utils.IMAGE_DIR, FILENAMES[name])).scaled(
            pixels, pixels, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        pixmap.setDevicePixelRatio(dpr)
        _cache[key] = pixmap

    return _cache[key]


# Size of the icons on buttons, and the gap between them and the button text, in pixels
BUTTON_ICON_SIZE = 18
BUTTON_ICON_GAP = 5

# Name of the Qt property that remembers a button's icon, so it can be tinted
# again when the colours change (see refreshButtonIcons)
_BUTTON_ICON_PROPERTY = "deepSpaceTraderIcon"


def tintedPixmap(name, size, dpr, color):
    """
    The icon 'name' (a white line drawing, e.g. STORE), 'size' pixels
    across, in 'color' (a QColor)
    """
    pixmap = QtGui.QPixmap(iconPixmap(name, size, dpr))
    painter = QtGui.QPainter(pixmap)
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return pixmap


def buttonIcon(name, palette, dpr=1.0):
    """
    The button icon 'name', in the colours of the button text in 'palette':
    normally, and greyed out for when the button is disabled. It has a
    see-through strip on its right, as a gap between it and the button text
    """
    icon = QtGui.QIcon()
    for mode, group in ((QtGui.QIcon.Normal, QtGui.QPalette.Active), (QtGui.QIcon.Disabled, QtGui.QPalette.Disabled)):
        color = palette.color(group, QtGui.QPalette.ButtonText)
        pixmap = QtGui.QPixmap(int(math.ceil((BUTTON_ICON_SIZE + BUTTON_ICON_GAP) * dpr)),
                               int(math.ceil(BUTTON_ICON_SIZE * dpr)))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.drawPixmap(0, 0, tintedPixmap(name, BUTTON_ICON_SIZE, dpr, color))
        painter.end()
        icon.addPixmap(pixmap, mode)

    return icon


def setButtonIcon(button, name):
    """
    Show the icon 'name' (e.g. STORE) on a button, next to its text, in the
    colour of the text
    """
    button.setProperty(_BUTTON_ICON_PROPERTY, name)
    button.setIconSize(QtCore.QSize(BUTTON_ICON_SIZE + BUTTON_ICON_GAP, BUTTON_ICON_SIZE))
    button.setIcon(buttonIcon(name, button.palette(), button.devicePixelRatioF()))


def refreshButtonIcons(widget):
    """
    Tint the icons of all buttons in 'widget' again, e.g. after the theme
    (and so the colour of button text) has changed
    """
    for button in widget.findChildren(QtWidgets.QAbstractButton):
        name = button.property(_BUTTON_ICON_PROPERTY)
        if name:
            button.setIcon(buttonIcon(name, button.palette(), button.devicePixelRatioF()))
