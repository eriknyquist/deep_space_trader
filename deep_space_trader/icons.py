"""
Icons for message boxes about special events (see utils.setMessageBoxIcon).
They're PNG files in the images folder, made by scripts/make_icons.py (which is
only needed to change them), and scaled down to the size they're shown at
"""
import os

from PyQt5 import QtCore, QtGui

# (utils imports this module, so IMAGE_DIR is looked up when it's needed, once utils is loaded)
from deep_space_trader import utils

# Icon names, passed to the dialog functions
PIRATES = "pirates"
CUSTOMS = "customs"
BLACK_MARKET = "black_market"

FILENAMES = {
    PIRATES: "event_pirates.png",
    CUSTOMS: "event_customs.png",
    BLACK_MARKET: "event_black_market.png",
}

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
