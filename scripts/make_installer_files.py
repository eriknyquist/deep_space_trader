"""
Make the files used by the Windows installer (setup.iss), and save them in
installer/:

- the large image on the left of the installer's first and last pages, and
  the small image at the top right of the other pages, at several sizes for
  high-DPI screens (BMP files, as Inno Setup needs)
- a copy of LICENSE that Inno Setup shows correctly (with a UTF-8 marker at the
  start: without it, the curly quotes in LICENSE show as gibberish)

Only needed when these should change, e.g. after changing LICENSE.

Usage (from the project folder):

    python scripts/make_installer_files.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from PyQt5 import QtCore, QtGui  # noqa: E402

from deep_space_trader import planet_image  # noqa: E402

OUTPUT = os.path.join(ROOT, "installer")
ICON = os.path.join(ROOT, "deep_space_trader", "images", "icon.png")
LICENSE = os.path.join(ROOT, "LICENSE")

# Sizes Inno Setup uses at 100%, 150% and 200% screen scaling
# (WizardImageFile and WizardSmallImageFile)
LARGE_SIZES = [(164, 314), (246, 459), (328, 628)]
SMALL_SIZES = [(55, 55), (83, 80), (110, 106)]

# The planet on the large image: one of the game's planet pictures, chosen
# for having a ring and a moon
PLANET_NAME = "Deep Space Trader"


def largeImage(width, height):
    """
    Dark space, with a planet in the middle and the game's name below it
    """
    image = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

    # The planet's own space (and stars), square and as tall as the image,
    # with its sides cut off, so the stars stay round
    recipe = planet_image.planetRecipe(PLANET_NAME)
    painter.save()
    painter.translate((width - height) / 2.0, 0)
    painter.scale(height / planet_image.GRID, height / planet_image.GRID)
    planet_image.drawSpace(painter, recipe)
    painter.restore()

    # Then the planet itself, with no background, in the upper middle
    side = width
    top = int(height * 0.18)
    painter.save()
    painter.translate(0, top)
    painter.scale(side / planet_image.GRID, side / planet_image.GRID)
    planet_image.drawPlanet(painter, recipe, background=False)
    painter.restore()

    font = QtGui.QFont("Arial")
    font.setBold(True)
    font.setPixelSize(int(width * 0.13))
    painter.setFont(font)
    painter.setPen(QtGui.QColor("#ffffff"))
    text = QtCore.QRect(0, top + side + int(height * 0.04), width, int(height * 0.25))
    painter.drawText(text, QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop | QtCore.Qt.TextWordWrap,
                     "Deep Space\nTrader")
    painter.end()
    return image


def smallImage(width, height):
    """
    The game's icon, on white (the background of the installer's page headers)
    """
    image = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
    image.fill(QtGui.QColor("#ffffff"))
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
    side = min(width, height)
    icon = QtGui.QImage(ICON).scaled(side, side, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    painter.drawImage((width - icon.width()) // 2, (height - icon.height()) // 2, icon)
    painter.end()
    return image


def main():
    app = QtGui.QGuiApplication.instance() or QtGui.QGuiApplication(sys.argv[:1])
    app.setApplicationName("make_installer_files")
    os.makedirs(OUTPUT, exist_ok=True)

    for width, height in LARGE_SIZES:
        path = os.path.join(OUTPUT, "wizard_image_%dx%d.bmp" % (width, height))
        largeImage(width, height).save(path)
        print("saved %s" % path)

    for width, height in SMALL_SIZES:
        path = os.path.join(OUTPUT, "wizard_small_image_%dx%d.bmp" % (width, height))
        smallImage(width, height).save(path)
        print("saved %s" % path)

    with open(LICENSE, "r", encoding="utf-8") as fh:
        text = fh.read()
    path = os.path.join(OUTPUT, "license.txt")
    with open(path, "w", encoding="utf-8-sig", newline="\r\n") as fh:
        fh.write(text)
    print("saved %s" % path)


if __name__ == "__main__":
    main()
