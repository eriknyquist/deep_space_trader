import random

from PyQt5 import QtWidgets, QtCore

from deep_space_trader.utils import yesNoDialog, errorDialog, infoDialog, ScrollableTextDisplay, percentChance
from deep_space_trader.game_state import State
from deep_space_trader.store import load_store_items
from deep_space_trader import constants as const
from deep_space_trader import config
from deep_space_trader.location_browser import LocationBrowser
from deep_space_trader.top_button_bar import ButtonBar
from deep_space_trader.high_scores import HighScoreTable, HighScoreSharing
from deep_space_trader.item_browsers import PlayerItemBrowser, PlanetItemBrowser, WarehouseItemBrowser
from deep_space_trader.item_prices import PricesTable
from deep_space_trader.star_map import StarMap
from deep_space_trader.information_bar import InfoBar
from deep_space_trader.sounds import AudioPlayer
from deep_space_trader.items import itemDisplayName
from deep_space_trader.i18n import translate, formatNumber


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
        self.state = State(self)
        self.audio = AudioPlayer()
        load_store_items(self)
        self.pending_price_anomaly = None
        self.temporary_price_change = None

        middleColumnLayout = QtWidgets.QHBoxLayout()

        self.locationBrowserGroup = QtWidgets.QGroupBox(self.tr("Planets ({0})").format(formatNumber(len(self.state.planets))))
        self.locationBrowserGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        planetsLayout = QtWidgets.QHBoxLayout()
        self.locationBrowser = LocationBrowser(self)
        planetsLayout.addWidget(self.locationBrowser)
        self.locationBrowserGroup.setLayout(planetsLayout)
        self.locationBrowserGroup.setAlignment(QtCore.Qt.AlignCenter)
        middleColumnLayout.addWidget(self.locationBrowserGroup)

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
        infoGroup = QtWidgets.QGroupBox(self.tr("Information"))
        infoGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        infoGroup.setAlignment(QtCore.Qt.AlignCenter)
        infoGroup.setLayout(infoLayout)
        infoGroup.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

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
        planetItemsBrowserGroup = QtWidgets.QGroupBox(self.tr("Items on current planet"))
        planetItemsBrowserGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        planetItemsBrowserGroup.setAlignment(QtCore.Qt.AlignCenter)
        planetItemsBrowserGroup.setLayout(planetItemsLayout)
        lastColumnLayout.addWidget(planetItemsBrowserGroup)

        warehouseItemsLayout = QtWidgets.QHBoxLayout()
        self.warehouseItemBrowser = WarehouseItemBrowser(self)
        warehouseItemsLayout.addWidget(self.warehouseItemBrowser)
        self.warehouseItemsBrowserGroup = QtWidgets.QGroupBox()
        self.warehouseItemsBrowserGroup.setStyleSheet("QGroupBox{ font-weight: bold; }")
        self.warehouseItemsBrowserGroup.setAlignment(QtCore.Qt.AlignCenter)
        self.warehouseItemsBrowserGroup.setLayout(warehouseItemsLayout)
        self.updateWarehouseLabel()
        lastColumnLayout.addWidget(self.warehouseItemsBrowserGroup)


        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(infoGroup)
        self.mainLayout.addWidget(buttonGroup)
        self.mainLayout.addLayout(middleColumnLayout)
        self.mainLayout.addLayout(lastColumnLayout)

        config.config_load()

    def updatePlanetsGroupBoxTitle(self, count=None):
        num_planets = len(self.state.planets) if count is None else count
        self.locationBrowserGroup.setTitle(self.tr("Planets ({0})").format(formatNumber(num_planets)))

    def enableSounds(self, enabled):
        self.audio.setEnabled(enabled)

    def enableTooltips(self, enabled):
        self.infoBar.enableTooltips(enabled)
        self.buttonBar.enableTooltips(enabled)
        self.locationBrowser.enableTooltips(enabled)
        self.playerItemBrowser.enableTooltips(enabled)
        self.planetItemBrowser.enableTooltips(enabled)
        self.warehouseItemBrowser.enableTooltips(enabled)

    def updatePlayerItemsLabel(self):
        self.playerItemBrowserGroup.setTitle(self.tr("Items on your ship ({0}/{1})").format(
                                             formatNumber(self.state.items.count()),
                                             formatNumber(self.state.capacity)))

    def updateWarehouseLabel(self):
        # The warehouse is on the home planet, which is different in every game
        self.warehouseItemsBrowserGroup.setTitle(self.tr("Items in warehouse (on {0})", "{0} is a planet name").format(
                                                 self.state.home_planet.full_name))

    def showTravelLog(self):
        dialog = ScrollableTextDisplay(self.tr("Travel log"), self.state.read_travel_log())
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def showTransactionLog(self):
        dialog = ScrollableTextDisplay(self.tr("Transaction log"), self.state.read_transaction_log())
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

    def showStarMap(self):
        dialog = StarMap(self)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def showPrices(self):
        dialog = PricesTable(self)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def warningBeforeQuit(self):
        return yesNoDialog(self, self.tr("Are you sure?"), self.tr("Are you sure you want to quit?"))

    def reset(self):
        load_store_items(self)
        self.state.initialize()
        self.infoBar.update()
        self.locationBrowser.update()
        self.playerItemBrowser.update()
        self.planetItemBrowser.update()
        self.warehouseItemBrowser.update()
        self.updatePlayerItemsLabel()
        self.updateWarehouseLabel()

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

            if percentChance(const.TRADING_TIP_ACCURACY_PERCENTAGE):
                if itemname in planet.items.items:
                    planet.update_prices(self.state.day)
                    item = planet.items.items[itemname]

                    self.temporary_price_change = (planet, itemname, item.value)
                    old_value = item.value
                    if increase:
                        # Increase price by 200-500%
                        change_percentage = random.randint(200, 500)
                        item.value += int((float(item.value) / 100.0) * float(change_percentage))
                    else:
                        # Decrease price by 80-95%
                        change_percentage = random.randint(80, 95)
                        item.value -= int((float(item.value) / 100.0) * float(change_percentage))

                    item.value_history[-1] = item.value

                    if planet is self.state.current_planet:
                        if increase:
                            msg = self.tr("The rumour you heard about {0} was true!<br><br>{0} prices "
                                          "are through the roof.", "{0} is an item name, e.g. tin")
                        else:
                            msg = self.tr("The rumour you heard about {0} was true!<br><br>{0} prices "
                                          "are at an all-time low.", "{0} is an item name, e.g. tin")

                        self.audio.play(self.audio.RumourTrueSound)
                        infoDialog(self, self.tr("Rumour was true!"), msg.format(itemDisplayName(itemname)))
            else:
                if planet is self.state.current_planet:
                    self.audio.play(self.audio.FailureSound)
                    infoDialog(self, self.tr("Rumour was false"),
                                     self.tr("The rumour you heard about {0} on {1} was false!",
                                             "{0} is an item name, e.g. tin, and {1} is a planet name").format(
                                             itemDisplayName(itemname), planet.full_name))

            return

        if self.temporary_price_change is not None:
            planet, itemname, old_value = self.temporary_price_change
            self.temporary_price_change = None

            if itemname in planet.items.items:
                planet.items.items[itemname].value = old_value

        if not percentChance(const.CHANCE_TRADING_TIP_PERCENTAGE):
            # Nothing to do this time
            return

        # Pick a random planet
        planet = random.choice(self.state.planets)

        # Pick a random item on that planet
        itemname = random.choice(list(planet.items.items.keys()))
        item = planet.items.items[itemname]

        # Will the price increase or decrease?
        increase = percentChance(50)

        if increase:
            msg = random.choice([
                self.tr("You hear a rumour that {0} will be very expensive on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
                self.tr("You hear a rumour that {0} will be extremely expensive on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
                self.tr("You hear a rumour that {0} will be unreasonably expensive on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
                self.tr("You hear a rumour that {0} will be unusually expensive on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
            ])
        else:
            msg = random.choice([
                self.tr("You hear a rumour that {0} will be very cheap on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
                self.tr("You hear a rumour that {0} will be extremely cheap on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
                self.tr("You hear a rumour that {0} will be unreasonably cheap on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
                self.tr("You hear a rumour that {0} will be unusually cheap on {1} tomorrow!",
                        "{0} is an item name, e.g. tin, and {1} is a planet name"),
            ])

        msg = msg.format(itemDisplayName(itemname), planet.full_name)

        self.audio.play(self.audio.RumourSound)
        infoDialog(self, self.tr("Rumour overheard!"), msg)
        self.pending_price_anomaly = (planet, itemname, increase)

    def advanceDay(self):
        if self.state.next_day():
            # Days remaining, check health
            if self.state.health == 0:
                self.audio.play(self.audio.DeathSound)
                infoDialog(self, self.tr("Dead!"), self.tr("You have starved to death."))
                self.checkHighScore()
                self.reset()
                return

            self.runRandomNotifications()
            self.state.current_planet.update_prices(self.state.day)
            self.infoBar.update()
            self.planetItemBrowser.update()
        else:
            # No days remaining
            infoDialog(self, self.tr("Game complete"), message=self.tr("Time is up!"))
            self.checkHighScore()
            self.reset()

    def checkHighScore(self):
        if self.state.money == 0:
            return

        scores = config.get_highscores()

        # High scores are sorted in descending order.
        # We only store up to constants.MAX_HIGH_SCORES high scores.
        if (len(scores) > 0) and (len(scores) == const.MAX_HIGH_SCORES) and (self.state.money <= scores[-1][1]):
            return

        proceed = yesNoDialog(self, self.tr("High score!"),
                              message=self.tr("You have achieved a high score ({0}) ! "
                                              "would you like to enter your name? (high "
                                              "scores are only stored locally)").format(formatNumber(self.state.money)),
                              cancelable=False)

        if not proceed:
            return

        initial_text = '' if len(scores) == 0 else scores[0][0]
        name = None

        while True:
            name, accepted = QtWidgets.QInputDialog.getText(self, self.tr("Enter name"),
                                                            self.tr("Enter your name for the high score table"),
                                                            text=initial_text)

            if not accepted:
                return

            if len(name) > const.MAX_HIGHSCORE_NAME_LEN:
                # (Counts passed to translate() must be plain variables, or pylupdate5 skips the string)
                max_len = const.MAX_HIGHSCORE_NAME_LEN
                errorDialog(self, self.tr("Too long"),
                            translate("MainWidget", "Name is too long (max %Ln characters)", None, max_len))
            else:
                break

        config.add_highscore(name, self.state.money)
        config.config_store()
        self.showHighScores()

    def sizeHint(self):
        return QtCore.QSize(800, 600)
