import os
import json
import zlib
import copy
import random
import traceback

from PyQt5 import QtWidgets, QtCore, QtGui

from deep_space_trader.utils import yesNoDialog, errorDialog, infoDialog, ScrollableTextDisplay
from deep_space_trader.game_state import State
from deep_space_trader.store import load_store_items
from deep_space_trader import constants as const
from deep_space_trader import config
from deep_space_trader.location_browser import LocationBrowser
from deep_space_trader.top_button_bar import ButtonBar
from deep_space_trader.high_scores import HighScoreTable, HighScoreSharing
from deep_space_trader.item_browsers import PlayerItemBrowser, PlanetItemBrowser, WarehouseItemBrowser
from deep_space_trader.item_prices import PricesTable
from deep_space_trader.information_bar import InfoBar


# Set checkbox state without triggering the stateChanged signal
def _silent_checkbox_set(checkbox, value, handler):
    checkbox.stateChanged.disconnect(handler)
    checkbox.setChecked(value)
    checkbox.stateChanged.connect(handler)

class MainWidget(QtWidgets.QDialog):
    def __init__(self, primaryScreen, mainWindow):
        super(MainWidget, self).__init__()
        self.main = mainWindow
        self.primary_screen = primaryScreen
        self.state = State()
        load_store_items()
        self.pending_price_anomaly = None
        self.temporary_price_change = None

        middleColumnLayout = QtWidgets.QHBoxLayout()

        planetsLayout = QtWidgets.QHBoxLayout()
        self.locationBrowser = LocationBrowser(self)
        planetsLayout.addWidget(self.locationBrowser)
        locationBrowserGroup = QtWidgets.QGroupBox("Planets")
        locationBrowserGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        locationBrowserGroup.setLayout(planetsLayout)
        locationBrowserGroup.setAlignment(QtCore.Qt.AlignCenter)
        middleColumnLayout.addWidget(locationBrowserGroup)

        playerItemsLayout = QtWidgets.QHBoxLayout()
        self.playerItemBrowser = PlayerItemBrowser(self)
        playerItemsLayout.addWidget(self.playerItemBrowser)
        self.playerItemBrowserGroup = QtWidgets.QGroupBox()
        self.playerItemBrowserGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        self.playerItemBrowserGroup.setLayout(playerItemsLayout)
        self.playerItemBrowserGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.updatePlayerItemsLabel()
        middleColumnLayout.addWidget(self.playerItemBrowserGroup)

        infoLayout = QtWidgets.QHBoxLayout()
        self.infoBar = InfoBar(self)
        infoLayout.addWidget(self.infoBar)
        infoGroup = QtWidgets.QGroupBox("Information")
        infoGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        infoGroup.setAlignment(QtCore.Qt.AlignCenter)
        infoGroup.setLayout(infoLayout)

        buttonLayout = QtWidgets.QHBoxLayout()
        self.buttonBar = ButtonBar(self)
        buttonLayout.addWidget(self.buttonBar)
        buttonGroup = QtWidgets.QGroupBox()
        buttonGroup.setAlignment(QtCore.Qt.AlignCenter)
        buttonGroup.setLayout(buttonLayout)

        lastColumnLayout = QtWidgets.QHBoxLayout()

        planetItemsLayout = QtWidgets.QHBoxLayout()
        self.planetItemBrowser = PlanetItemBrowser(self)
        planetItemsLayout.addWidget(self.planetItemBrowser)
        planetItemsBrowserGroup = QtWidgets.QGroupBox("Items on current planet")
        planetItemsBrowserGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        planetItemsBrowserGroup.setAlignment(QtCore.Qt.AlignCenter)
        planetItemsBrowserGroup.setLayout(planetItemsLayout)
        lastColumnLayout.addWidget(planetItemsBrowserGroup)

        warehouseItemsLayout = QtWidgets.QHBoxLayout()
        self.warehouseItemBrowser = WarehouseItemBrowser(self)
        warehouseItemsLayout.addWidget(self.warehouseItemBrowser)
        warehouseItemsBrowserGroup = QtWidgets.QGroupBox("Items in warehouse")
        warehouseItemsBrowserGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        warehouseItemsBrowserGroup.setAlignment(QtCore.Qt.AlignCenter)
        warehouseItemsBrowserGroup.setLayout(warehouseItemsLayout)
        lastColumnLayout.addWidget(warehouseItemsBrowserGroup)


        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(infoGroup)
        self.mainLayout.addWidget(buttonGroup)
        self.mainLayout.addLayout(middleColumnLayout)
        self.mainLayout.addLayout(lastColumnLayout)

        config.config_load()

    def updatePlayerItemsLabel(self):
        self.playerItemBrowserGroup.setTitle("Items on your ship ({0:,}/{1:,})".format(
                                             self.state.items.count(),
                                             self.state.capacity))

    def showTravelLog(self):
        dialog = ScrollableTextDisplay("Travel log", self.state.read_travel_log())
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def showHighScores(self):
        dialog = HighScoreTable(self)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def shareHighScores(self):
        dialog = HighScoreSharing(self)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def showPrices(self):
        dialog = PricesTable(self)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def warningBeforeQuit(self):
        return yesNoDialog(self, "Are you sure?", "Are you sure you want to quit?")

    def reset(self):
        load_store_items()
        self.state.initialize()
        self.infoBar.update()
        self.locationBrowser.update()
        self.playerItemBrowser.update()
        self.planetItemBrowser.update()
        self.warehouseItemBrowser.update()
        self.updatePlayerItemsLabel()

    def quit(self):
        if self.warningBeforeQuit():
            config.config_store()
            QtWidgets.qApp.quit()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.quit()

    def runRandomNotifications(self):
        if self.pending_price_anomaly is not None:
            planet, itemname, increase = self.pending_price_anomaly
            self.pending_price_anomaly = None

            if random.randint(0, 100) <= const.TRADING_TIP_ACCURACY_PERCENTAGE:
                if itemname in planet.items.items:
                    item = planet.items.items[itemname]

                    self.temporary_price_change = (planet, itemname, item.value)
                    old_value = item.value
                    if increase:
                        # Increase price by 100-500%
                        change_percentage = random.randint(200, 500)
                        item.value += int((float(item.value) / 100.0) * float(change_percentage))
                    else:
                        # Decrease price by 70-90%
                        change_percentage = random.randint(80, 95)
                        item.value -= int((float(item.value) / 100.0) * float(change_percentage))

                    if planet is self.state.current_planet:
                        infoDialog(self, "Rumour was true!",
                                   "The rumour you heard about %s was true!<br><br>%s prices are %s."
                                   % (itemname, itemname, "through the roof" if increase else "at an all-time low"))
            else:
                if planet is self.state.current_planet:
                    infoDialog(self, "Rumour was false",
                                     "The rumour you heard about %s on %s was false!" % (itemname, planet.full_name))

            return

        if self.temporary_price_change is not None:
            planet, itemname, old_value = self.temporary_price_change
            self.temporary_price_change = None

            if itemname in planet.items.items:
                planet.items.items[itemname].value = old_value

        if random.randint(0, 100) > const.CHANCE_TRADING_TIP_PERCENTAGE:
            # Nothing to do this time
            return

        # Pick a random planet
        planet = random.choice(self.state.planets)

        # Pick a random item on that planet
        itemname = random.choice(list(planet.items.items.keys()))
        item = planet.items.items[itemname]

        # Will the price increase or decrease?
        increase = random.randint(0, 100) >= 50

        adj = random.choice(["very", "extremely", "unreasonably", "unusually"])
        descriptor = "expensive" if increase else "cheap"

        msg = (
            "You hear a rumour that %s will be %s %s on %s tomorrow!"
            % (itemname, adj, descriptor, planet.full_name)
        )

        infoDialog(self, "Rumour overheard!", msg)
        self.pending_price_anomaly = (planet, itemname, increase)

    def advanceDay(self):
        if self.state.next_day():
            # Days remaining
            self.runRandomNotifications()
            self.state.update_planet_item_prices()
            self.infoBar.update()
            self.planetItemBrowser.update()
        else:
            # No days remaining
            infoDialog(self, "Game complete", message="Time is up!")
            self.checkHighScore()
            self.reset()

    def checkHighScore(self):
        scores = config.get_highscores()

        # High scores are sorted in descending order
        if (len(scores) > 0) and (self.state.money <= scores[0][1]):
            return

        proceed = yesNoDialog(self, "High score!",
                              message="You have achieved a high score ({:,}) ! "
                                      "would you like to enter your name? (high "
                                      "scores are only stored locally)".format(self.state.money))

        if not proceed:
            return

        initial_text = '' if len(scores) == 0 else scores[0][0]
        name = None

        while True:
            name, accepted = QtWidgets.QInputDialog.getText(self, 'Enter name',
                                                            "Enter your name for the high score table",
                                                            text=initial_text)

            if not accepted:
                return

            if len(name) > const.MAX_HIGHSCORE_NAME_LEN:
                errorDialog(self, "Too long", "Name is too long (max %d characters)"
                                  % const.MAX_HIGHSCORE_NAME_LEN)
            else:
                break

        config.add_highscore(name, self.state.money)
        config.config_store()
        self.showHighScores()

    def sizeHint(self):
        return QtCore.QSize(1920, 1080)
