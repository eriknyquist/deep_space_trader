"""
Make the screenshots used in README.rst.

Sets up a game part-way through, opens every window shown in the README, and
saves a screenshot of each one in images/. Windows and dialogs are captured
from the screen, with their title bars, so run this on a desktop (the images in
the README were taken on Windows). The game's windows briefly appear while this
runs; don't cover them with other windows until it finishes.

Usage (from the project folder):

    python scripts/make_readme_images.py                  # all images, saved in images/
    python scripts/make_readme_images.py --output preview # save them somewhere else
    python scripts/make_readme_images.py --only store star_map

Your settings don't affect the images: the game uses the default values from
constants.py whatever INITIAL_PLANET_COUNT etc. are set to, English text, a
temporary config file (your real high scores aren't touched), and no sounds.
"""
import argparse
import importlib
import os
import random
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from PyQt5 import QtWidgets, QtCore, QtTest

from deep_space_trader import constants as const

# Same starting values for everyone, whatever constants.py has been changed to locally
const.INITIAL_PLANET_COUNT = 8
const.INITIAL_MONEY = 2000
const.FORCE_LANGUAGE = None


class SilentAudio(object):
    """
    Stands in for the sound player: no sounds, and no waiting for them to load
    """
    def __getattr__(self, name):
        if name.endswith("Sound"):
            return name
        raise AttributeError(name)

    def play(self, sound):
        pass

    def setEnabled(self, enabled):
        pass


try:
    importlib.import_module("deep_space_trader.sounds")
except ImportError:
    # QtMultimedia isn't available; no sounds are needed anyway
    sys.modules["deep_space_trader.sounds"] = types.SimpleNamespace(
        AudioPlayer=SilentAudio, waitForSounds=lambda parent, audio: None)

from deep_space_trader import config, main_widget  # noqa: E402
from deep_space_trader.items import ItemCollection, Items, common_item_types, medium_rare_item_types  # noqa: E402

DEFAULT_OUTPUT = os.path.join(os.path.dirname(HERE), "images")

# Window sizes, as in the earlier README images (other windows keep their own size)
DIALOG_SIZES = {
    "store": (1040, 560),
    "price_graph_window": (664, 600),
    "material_prices_window": (600, 437),
    "travel_log_window": (480, 245),
    "transaction_log_window": (520, 245),
    "high_score_sharing_window": (1000, 569),
    "trading_console": (600, 432),
    "star_map": (900, 760),
}


class Screenshots(object):
    """
    Opens each window shown in the README, and saves a screenshot of it
    """
    def __init__(self, app, output, only):
        self.app = app
        self.output = output
        self.only = set(only) if only else None
        self.pending = None
        self.saved = []

        # Dialogs are normally opened with exec_(), which waits until they're
        # closed. Instead, take the screenshot and close them straight away
        QtWidgets.QDialog.exec_ = lambda dialog: self.captureDialog(dialog)
        QtWidgets.QMessageBox.exec_ = lambda dialog: self.captureDialog(dialog)

    def wanted(self, name):
        return (self.only is None) or (name in self.only)

    def settle(self, ms=400):
        """
        Give windows time to appear and be drawn (the window manager draws title bars)
        """
        self.app.processEvents()
        QtTest.QTest.qWait(ms)
        self.app.processEvents()

    def save(self, name, pixmap):
        path = os.path.join(self.output, name + ".png")
        pixmap.save(path)
        self.saved.append(path)
        print("saved %s (%dx%d)" % (path, pixmap.width(), pixmap.height()))

    def grabWithFrame(self, window):
        """
        Screenshot of a window including its title bar, taken from the screen.
        Without a real screen (e.g. QT_QPA_PLATFORM=offscreen), the window
        is drawn without a title bar instead
        """
        window.raise_()
        window.activateWindow()
        self.settle()

        if self.app.platformName() in ("offscreen", "minimal"):
            return window.grab()

        frame = window.frameGeometry()
        screen = window.screen()
        origin = screen.geometry().topLeft()
        return screen.grabWindow(0, frame.x() - origin.x(), frame.y() - origin.y(), frame.width(), frame.height())

    def captureDialog(self, dialog):
        """
        Replaces QDialog.exec_(): shows the dialog, saves a screenshot of it if
        one is wanted, and closes it
        """
        name, self.pending = self.pending, None
        if (name is not None) and self.wanted(name):
            if name in DIALOG_SIZES:
                dialog.resize(*DIALOG_SIZES[name])
            dialog.show()
            self.save(name, self.grabWithFrame(dialog))

        dialog.close()
        dialog.deleteLater()
        return 0

    def dialog(self, name, opener):
        """
        Call 'opener', which opens a dialog with exec_(), and save the dialog as 'name'
        """
        if not self.wanted(name):
            return

        self.pending = name
        opener()
        if self.pending is not None:
            self.pending = None
            raise RuntimeError("%s: no dialog was opened" % name)

    def section(self, name, widget):
        """
        Save part of the main window (no title bar)
        """
        if self.wanted(name):
            self.save(name, widget.grab())


def give(collection, itemname, quantity, value):
    """
    Add some items of one type to a collection, at a given value
    """
    item_type = next(t for t in common_item_types + medium_rare_item_types if t.name == itemname)
    collection.add_items(itemname, ItemCollection([Items(item_type, quantity, value)]), quantity)


def setUpGame(game):
    """
    A game part-way through: a few scout expeditions, upgrades, a journey
    around the nearby planets, and items on the ship and in the warehouse
    """
    from deep_space_trader import store

    random.seed(1234)
    game.reset()
    state = game.state

    # Buy upgrades and scout expeditions through the store, so that the store
    # shows them as bought (e.g. "Upgrade scout fleet" rather than "Buy scout fleet")
    store.yesNoDialog = lambda *args, **kwargs: True
    state.money = 10 ** 12
    state.max_store_purchases_per_day = 1000
    shop = store.Store(game)
    item = {type(i): i for i in store.store_items}
    purchases = [store.CapacityIncrease] * 4 + [store.ScoutFleetUpgrade, store.PlanetExploration,
                 store.ScoutFleetUpgrade, store.PlanetExploration, store.ScoutFleetUpgrade,
                 store.PlanetExploration, store.PlanetExploration] + \
                [store.BattleFleetUpgrade] * 2 + [store.EngineUpgrade] * 3 + [store.TradingConsole]
    for purchase in purchases:
        shop.buyItem(item[purchase])
    shop.deleteLater()
    state.max_store_purchases_per_day = const.MAX_STORE_PURCHASES_PER_DAY

    # A trip around nearby planets and back home, trading along the way
    home = state.home_planet
    nearby = sorted(state.planets[1:], key=lambda p: p.distance_to(home))
    stops = [nearby[i] for i in (2, 9, 5, 14, 7, 20, 11)]

    # A few planets destroyed early on, so that reputation (the info bar, the
    # planets table and the star map tooltip) has something to show
    target = nearby[25]
    destroyed = [target] + sorted((p for p in nearby if p is not target and p not in stops),
                                  key=lambda p: p.distance_to(target))[:2]
    state.planets_destroyed(destroyed)
    for planet in destroyed:
        state.planets.remove(planet)
    for stop in stops + [home]:
        stop.update_prices(state.day)
        names = sorted(stop.items.items)
        if names:
            item = stop.items.items[names[0]]
            state.record_purchase(names[0], 250, item.value)
            if len(names) > 1:
                state.record_sale(names[1], 120, stop.items.items[names[1]].value)
                state.sold_to(stop)

        state.next_day()
        state.change_current_planet(stop)

    home.update_prices(state.day)
    state.money = 48250000
    state.health = 100
    state.store_purchases = 1
    state.warehouse_trips = 1

    # Items on the ship: some that the home planet trades, so they can be sold
    for name in sorted(home.items.items)[:2]:
        give(state.items, name, 400, home.items.items[name].value)
    give(state.items, "tin", 320, 10)

    for name, quantity in (("tin", 52000), ("copper", 31000), ("gold", 8400), ("silver", 22000),
                           ("uranium", 3100), ("plutonium", 940), ("steel", 47000)):
        give(state.warehouse, name, quantity, 20)

    config.config[config.SCORES_KEY] = [["Kim", 812440125], ["Ash", 204118900], ["Sam", 98030550],
                                        ["Lee", 41250000], ["Ana", 7920113]]

    game.infoBar.update()
    game.locationBrowser.update()
    game.playerItemBrowser.update()
    game.planetItemBrowser.update()
    game.warehouseItemBrowser.update()
    game.updatePlayerItemsLabel()
    game.updateWarehouseLabel()

    # Nearest planets first (the current planet, in green, at the top), with a planet selected
    table = game.locationBrowser.table
    table.sortItems(2)
    table.setCurrentCell(2, 0)
    table.scrollToTop()


def selectFirstRow(browser, itemname=None):
    table = browser.table
    for row in range(table.rowCount()):
        if (itemname is None) or (table.item(row, 0).data(QtCore.Qt.UserRole) == itemname):
            table.setCurrentCell(row, 0)
            return

    raise RuntimeError("%s is not in the table" % itemname)


def makeImages(shots):
    from deep_space_trader.__main__ import MainWindow
    from deep_space_trader import __version__ as version

    window = MainWindow(shots.app.primaryScreen())
    window.setWindowTitle("Deep Space Trader %s" % version)
    window.enableDarkTheme(True)
    window.resize(1135, 960)
    window.move(40, 40)
    window.show()

    game = window.widget
    setUpGame(game)
    shots.settle()
    state = game.state

    # The whole window, and its sections
    if shots.wanted("readme_image"):
        shots.save("readme_image", shots.grabWithFrame(window))

    shots.section("information_section", game.infoBar.parentWidget())
    shots.section("global_buttons_section", game.buttonBar.parentWidget())
    shots.section("planets_section", game.locationBrowserGroup)
    shots.section("planet_items_section", game.planetItemBrowser.parentWidget())
    shots.section("ship_items_section", game.playerItemBrowserGroup)
    shots.section("warehouse_section", game.warehouseItemsBrowserGroup)

    # Windows opened from the main window
    shots.dialog("store", game.buttonBar.storeButtonClicked)

    traded = sorted(state.current_planet.items.items)[0]
    selectFirstRow(game.planetItemBrowser, traded)
    shots.dialog("buy_window", game.planetItemBrowser.buyButtonClicked)

    # The most valuable item has the most interesting price history
    items = state.current_planet.items.items
    selectFirstRow(game.planetItemBrowser, max(items, key=lambda name: items[name].type.base_value))
    shots.dialog("price_graph_window",
                 lambda: QtTest.QTest.keyClick(game.planetItemBrowser, QtCore.Qt.Key_Return))

    selectFirstRow(game.playerItemBrowser, traded)
    shots.dialog("sell_window", game.playerItemBrowser.sellButtonClicked)
    shots.dialog("dump_ship_window", game.playerItemBrowser.dumpButtonClicked)
    shots.dialog("to_warehouse_window", game.playerItemBrowser.warehouseButtonClicked)

    selectFirstRow(game.warehouseItemBrowser, "tin")
    shots.dialog("from_warehouse_window", game.warehouseItemBrowser.removeButtonClicked)
    shots.dialog("dump_warehouse_window", game.warehouseItemBrowser.dumpButtonClicked)

    shots.dialog("material_prices_window", game.showPrices)
    shots.dialog("travel_log_window", game.showTravelLog)
    shots.dialog("transaction_log_window", game.showTransactionLog)
    shots.dialog("high_score_sharing_window", game.shareHighScores)

    table = game.locationBrowser.table
    table.setCurrentCell(3, 0)
    shots.dialog("trading_console", game.locationBrowser.pricesButtonClicked)
    shots.dialog("star_map", game.showStarMap)

    # A rumour, and the next day's news about it
    rolls = []
    main_widget.percentChance = lambda percent: rolls.pop(0)
    rumoured = sorted(state.current_planet.items.items)[-1]
    original_choice = random.choice

    def choose(options):
        # The rumour's planet, item and wording
        if options and isinstance(options[0], str) and options[0].startswith("You hear"):
            return options[0]
        if options is state.planets:
            return state.current_planet
        if rumoured in options:
            return rumoured
        return original_choice(options)

    main_widget.random.choice = choose
    rolls[:] = [True, True]
    shots.dialog("rumour", game.runRandomNotifications)
    rolls[:] = [True]
    shots.dialog("rumour_result", game.runRandomNotifications)
    main_widget.random.choice = original_choice

    # Not close(): that asks "Are you sure you want to quit?"
    window.hide()


def main():
    parser = argparse.ArgumentParser(description="Make the screenshots used in README.rst")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="folder to save the images in (default: images/)")
    parser.add_argument("--only", nargs="+", metavar="NAME",
                        help="only make these images (names without .png, e.g. store star_map)")
    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)

    # A temporary config file, so the player's real high scores aren't read or changed
    config.FILENAME = os.path.join(tempfile.mkdtemp(), "config.json")
    main_widget.AudioPlayer = SilentAudio

    # The same look as the game (see main() in __main__.py)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    font = app.font()
    font.setPointSize(12)
    font.setFamily('monospace')
    app.setFont(font)

    shots = Screenshots(app, args.output, args.only)
    makeImages(shots)
    print("%d images saved" % len(shots.saved))


if __name__ == "__main__":
    main()
