import random

import numpy

from deep_space_trader.utils import (
    errorDialog, yesNoDialog, infoDialog, selectedRowKey, selectRowByKey, percentChance
)
from deep_space_trader.item_browsers import TradingConsolePlanetDisplay
from deep_space_trader.i18n import translate, formatNumber, formatDistance
from deep_space_trader import reputation

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QT_TRANSLATE_NOOP

# Translated when used, since translations aren't loaded yet when this module is imported
TRADING_CONSOLE_MESSAGE = QT_TRANSLATE_NOOP("LocationBrowser",
                                            "You must buy the trading console from the store if "
                                            "you want to be able to see planet item prices without "
                                            "travelling to the planet")


class TradingConsole(QtWidgets.QDialog):
    def __init__(self, parent, planet):
        super(TradingConsole, self).__init__(parent)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        planet.update_prices(parent.state.day)
        self.mainLayout.addWidget(TradingConsolePlanetDisplay(parent, planet))
        self.setLayout(self.mainLayout)
        self.update()
        self.adjustSize()
        self.setWindowTitle(self.tr("Item prices on {0}", "{0} is a planet name").format(planet.full_name))

    def sizeHint(self):
        return QtCore.QSize(600, 400)


class DistanceDelegate(QtWidgets.QStyledItemDelegate):
    """
    Shows distances as text (e.g. "27.4 ly"). The cells store the distance as
    a number, so that Qt can sort thousands of rows quickly, without calling
    Python code for every comparison; the text is only made for visible rows
    """
    def displayText(self, value, locale):
        return formatDistance(value)


class ReputationDelegate(QtWidgets.QStyledItemDelegate):
    """
    Shows reputations as text (e.g. "Wary (58)"), for the same reason as DistanceDelegate
    """
    def displayText(self, value, locale):
        return reputation.describe(value)


# Columns of the planets table
NAME_COLUMN = 0
VISITED_COLUMN = 1
DISTANCE_COLUMN = 2
REPUTATION_COLUMN = 3


class LocationBrowser(QtWidgets.QWidget):
    def __init__(self, parent):
        super(LocationBrowser, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.planetSearchLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.toolButtonLayout = QtWidgets.QHBoxLayout()

        self.planetSearchText = QtWidgets.QLineEdit()
        self.planetSearchText.setPlaceholderText(self.tr("Search for planets by name..."))
        self.planetSearchText.textChanged.connect(self.planetSearchTextChanged)
        self.planetSearchLayout.addWidget(self.planetSearchText)

        self.travelButton = QtWidgets.QPushButton(self.tr("Travel..."))
        self.travelButton.clicked.connect(self.travelButtonClicked)
        self.buttonLayout.addWidget(self.travelButton)

        self.previousButton = QtWidgets.QPushButton(self.tr("Travel to previous"))
        self.previousButton.clicked.connect(self.previousButtonClicked)
        self.buttonLayout.addWidget(self.previousButton)

        self.homeButton = QtWidgets.QPushButton(self.tr("Travel home"))
        self.homeButton.clicked.connect(self.homeButtonClicked)
        self.buttonLayout.addWidget(self.homeButton)

        self.pricesButton = QtWidgets.QPushButton(self.tr("Trading console"))
        self.pricesButton.clicked.connect(self.pricesButtonClicked)
        self.toolButtonLayout.addWidget(self.pricesButton)
        self.pricesButton.setEnabled(self.parent.state.have_trading_console)

        self.starMapButton = QtWidgets.QPushButton(self.tr("Star map..."))
        self.starMapButton.clicked.connect(self.parent.showStarMap)
        self.toolButtonLayout.addWidget(self.starMapButton)

        self.table = QtWidgets.QTableWidget()

        # Set alternating row colors, but keep default highlight color...
        default_palette = self.table.palette()
        default_highlight = default_palette.color(QtGui.QPalette.Highlight)
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Highlight, default_highlight)
        self.table.setPalette(palette)

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([self.tr('Planet'), self.tr('visited?'), self.tr('Distance'),
                                              self.tr('Reputation')])
        self.table.verticalHeader().setVisible(False)
        # One line per planet: text that doesn't fit (e.g. "Refuses to trade (0)") is cut short with "..."
        self.table.setWordWrap(False)
        # Clicking a column header sorts by that column (e.g. by distance)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.onDoubleClick)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

        self.distanceDelegate = DistanceDelegate(self.table)
        self.table.setItemDelegateForColumn(DISTANCE_COLUMN, self.distanceDelegate)
        self.reputationDelegate = ReputationDelegate(self.table)
        self.table.setItemDelegateForColumn(REPUTATION_COLUMN, self.reputationDelegate)

        self.mainLayout.addLayout(self.planetSearchLayout)
        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addLayout(self.toolButtonLayout)
        self.mainLayout.addWidget(self.table)

        self.tradingConsoleTooltip = translate("LocationBrowser", TRADING_CONSOLE_MESSAGE)
        self.tooltipsEnabled = True
        self.setTooltips()
        self.table.resizeColumnsToContents()
        self.update()

    def enableTooltips(self, enabled):
        self.tooltipsEnabled = enabled
        self.setTooltips()

    def setTooltips(self):
        if self.tooltipsEnabled:
            self.travelButton.setToolTip(self.tr("travel to the selected planet"))
            self.previousButton.setToolTip(self.tr("travel back to the planet you were on before the current planet"))
            self.homeButton.setToolTip(self.tr("travel back to your home planet, where your warehouse is"))
            self.pricesButton.setToolTip(self.tradingConsoleTooltip)
            self.starMapButton.setToolTip(self.tr("show a map of all the planets you have discovered"))
        else:
            self.travelButton.setToolTip(None)
            self.previousButton.setToolTip(None)
            self.homeButton.setToolTip(None)
            self.pricesButton.setToolTip(None)
            self.starMapButton.setToolTip(None)

    def enableTradingConsole(self):
        self.pricesButton.setEnabled(True)
        self.tradingConsoleTooltip = self.tr("opens the trading console for the selected planet, "
                                             "allowing you to see item prices without travelling there")
        self.pricesButton.setToolTip(self.tradingConsoleTooltip)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self.enterPressed(self.selectedPlanet())

    def enterPressed(self, planet):
        """
        What the Enter key does, here and on the star map: open the trading
        console for 'planet' (None if no planet is selected), if the player
        has bought it
        """
        if self.parent.state.have_trading_console:
            if planet is None:
                return

            self.openTradingConsole(planet)
        else:
            errorDialog(self, message=translate("LocationBrowser", TRADING_CONSOLE_MESSAGE))

    def planetSearchTextChanged(self, newText):
        self.update()

    def filteredPlanets(self):
        """
        Planets matching the text in the search box, or all planets if it's empty
        """
        text = self.planetSearchText.text().strip().lower()
        if not text:
            return self.parent.state.planets

        return [planet for planet in self.parent.state.planets if text in planet.full_name.lower()]

    def colorPreviousPlanets(self):
        colors = [
            QtGui.QColor(0, 0xAA, 0, 50),
            QtGui.QColor(0, 0xAA, 0, 125),
        ]

        columns = self.table.columnCount()

        # Rows are found by planet, since the table may be sorted, or filtered by
        # the search box. Planets hidden by the filter have no row, and are skipped
        tail_row = self.rowOf(self.parent.state.previous_planets_tail)
        if tail_row is not None:
            for col in range(columns):
                self.table.item(tail_row, col).setBackground(QtGui.QBrush())

        self.table.setAlternatingRowColors(False)
        self.table.setAlternatingRowColors(True)

        for planet in self.parent.state.previous_planets:
            if planet not in self.parent.state.planets:
                # Destroyed
                continue

            color = colors.pop()
            row = self.rowOf(planet)
            if row is not None:
                for col in range(columns):
                    self.table.item(row, col).setBackground(color)

        row = self.rowOf(self.parent.state.current_planet)
        if row is None:
            return

        # Set current planet "visited=yes"
        item2 = QtWidgets.QTableWidgetItem(self.tr("yes"))
        item2.setTextAlignment(QtCore.Qt.AlignHCenter)
        self.table.setItem(row, 1, item2)

        # Set current planet row color
        for col in range(columns):
            self.table.item(row, col).setBackground(QtGui.QColor(0, 0xAA, 0))

    def rowTexts(self):
        """
        Text used in every row, looked up once per refresh rather than once per
        row (there can be 20,000 rows)
        """
        return {"yes": self.tr("yes"), "no": self.tr("no")}

    def reputationKey(self):
        """
        Identifies the reputations currently shown in the table: the same key means nothing has changed
        """
        reputation = self.parent.state.reputation
        return (id(reputation), reputation.version)

    def shownReputations(self, planets):
        """
        Reputations as stored in the table. Rounded, so that changes too small
        to matter (e.g. long after an event, far away) don't cause any refreshing
        """
        return numpy.round(self.parent.state.reputations(planets), 2)

    def rowOf(self, planet):
        """
        Row of a planet in the table, or None if it isn't in the table (e.g. hidden by the search box)
        """
        index = self.planetIndex.get(id(planet))
        if index is None:
            return None

        return self.table.row(self.nameItems[index])

    @staticmethod
    def numberCell(value):
        """
        Cell holding a number, shown as text by a delegate. Qt sorts these
        without calling Python code, which matters with thousands of rows
        """
        item = QtWidgets.QTableWidgetItem()
        item.setData(QtCore.Qt.DisplayRole, float(value))
        item.setTextAlignment(QtCore.Qt.AlignHCenter)
        return item

    def addRow(self, planet, row, texts, planet_reputation):
        item1 = QtWidgets.QTableWidgetItem(planet.full_name)
        # Keep a reference to the planet on the row, so the planet can be found
        # without looking it up by name or by row number
        item1.setData(QtCore.Qt.UserRole, planet)
        item2 = QtWidgets.QTableWidgetItem(texts["yes"] if planet.visited else texts["no"])
        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        item3 = self.numberCell(self.parent.state.current_planet.distance_to(planet))
        item4 = self.numberCell(planet_reputation)

        if planet is self.parent.state.home_planet:
            font = item1.font()
            font.setBold(True)
            item1.setFont(font)
            item1.setToolTip(self.tr("Your home planet. Your warehouse is here."))

        self.table.setItem(row, 0, item1)
        self.table.setItem(row, 1, item2)
        self.table.setItem(row, 2, item3)
        self.table.setItem(row, 3, item4)

    def populateTable(self, planets):
        selectedKey = selectedRowKey(self.table)
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)

        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setRowCount(len(planets))
        texts = self.rowTexts()

        # What the table shows, in the order 'planets' were added. Each row's
        # name cell stays the same when the table is sorted, so it's used to find
        # the row that a planet has moved to
        self.tablePlanets = list(planets)
        self.planetIndex = {id(planet): i for i, planet in enumerate(planets)}
        self.tableReputations = self.shownReputations(planets)
        self.shownReputationKey = self.reputationKey()

        for row in range(len(planets)):
            self.addRow(planets[row], row, texts, self.tableReputations[row])

        self.nameItems = [self.table.item(row, 0) for row in range(len(planets))]
        self.nameItemIndex = {id(item): i for i, item in enumerate(self.nameItems)}

        self.table.setSortingEnabled(True)
        selectRowByKey(self.table, selectedKey)
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)

        self.parent.updatePlanetsGroupBoxTitle(len(planets))

    def refreshDistances(self):
        """
        Update the distance and reputation columns and colours after
        travelling (reputation changes every day). Much faster than rebuilding
        the table (update) when there are thousands of planets
        """
        current = self.parent.state.current_planet
        self.refreshColumns(lambda planets: [current.distance_to(p) for p in planets], DISTANCE_COLUMN)

    def refreshReputations(self):
        """
        Update the reputation column, e.g. after selling, which improves the opinion of nearby planets
        """
        self.refreshColumns(None, None)

    def refreshColumns(self, values, column):
        """
        Update the reputation column, and 'column' with 'values(planets)' if given
        """
        table = self.table

        # Only reputations that have changed. Planets far from anything the
        # player has done keep the same reputation, so usually most cells are
        # left alone, and when nothing has changed no cells are even looked at,
        # which matters with thousands of planets
        changed = []
        if self.reputationKey() != self.shownReputationKey:
            reputations = self.shownReputations(self.tablePlanets)
            changed = numpy.nonzero(reputations != self.tableReputations)[0]
            self.tableReputations = reputations
            self.shownReputationKey = self.reputationKey()

        if (values is None) and (len(changed) == 0):
            return

        # Index (in self.tablePlanets) of the planet in each row
        indexes = [self.nameItemIndex[id(table.item(row, 0))] for row in range(table.rowCount())]

        changes = {}
        if len(changed) > 0:
            rows = numpy.empty(len(indexes), dtype=int)
            rows[indexes] = numpy.arange(len(indexes))
            changes[REPUTATION_COLUMN] = [(rows[i], reputations[i]) for i in changed]

        if values is not None:
            changes[column] = list(enumerate(values([self.tablePlanets[i] for i in indexes])))

        model = table.model()
        table.setUpdatesEnabled(False)
        table.setSortingEnabled(False)

        # The view would otherwise handle a "data changed" signal for every cell
        model.blockSignals(True)
        for column, column_changes in changes.items():
            for row, value in column_changes:
                # A new cell, rather than changing the old one: after sorting, Qt
                # searches the whole table to find a changed cell's position
                table.setItem(row, column, self.numberCell(value))
        model.blockSignals(False)

        # Sorts once, by the current sort column, if there is one
        self.table.setSortingEnabled(True)
        self.table.setUpdatesEnabled(True)
        self.table.viewport().update()
        self.colorPreviousPlanets()

    def update(self):
        # Keep the search filter, so the table always matches the search box
        self.populateTable(self.filteredPlanets())
        self.colorPreviousPlanets()
        super(LocationBrowser, self).update()

    def selectedPlanet(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            return None

        return self.table.item(selectedRow, 0).data(QtCore.Qt.UserRole)

    def travelToPlanet(self, planet):
        planetname = planet.full_name
        if planet is self.parent.state.current_planet:
            errorDialog(self, message=self.tr("You are already on {0}!", "{0} is a planet name").format(planetname))
            return

        cost = self.parent.state.travel_cost_to(planet)
        if self.parent.state.money < cost:
            errorDialog(self, message=self.tr("You don't have enough money! ({0} required)").format(
                                      formatNumber(cost)))
            return

        distance = self.parent.state.current_planet.distance_to(planet)
        accepted = yesNoDialog(self, self.tr("Travel"),
                               self.tr("Travel to {0}?<br><br>(distance {1}, cost {2}, you have {3})",
                                       "{0} is a planet name, and {1} is a distance, e.g. 27.4 ly").format(
                               planetname, formatDistance(distance), formatNumber(cost),
                               formatNumber(self.parent.state.money)))
        if not accepted:
            return

        self.parent.state.money -= cost

        if percentChance(self.parent.state.pirate_chance(planet)):
            self.parent.audio.play(self.parent.audio.BattleSound)
            accepted = yesNoDialog(self, self.tr("Attacked by pirates!"),
                                   self.tr("You have encountered a pirate fleet while travelling "
                                           "between planets!<br><br>Your battle fleet must defeat them if "
                                           "you want to continue.<br><br>"
                                           "If you fight and lose, you will die.<br><br>"
                                           "If you fight and win, you will lose some health, but you will "
                                           "be able to continue your travels and will not lose any money "
                                           "or resources.<br><br>"
                                           "If you do not fight, then the only other "
                                           "option is surrender; you will not die or lose any health, but you "
                                           "may lose some of your money and resources.<br><br>Do you want to fight?"),
                                   cancelable=False)
            if accepted:
                battle_won = self.parent.state.battle_won()
                if battle_won:
                    self.parent.state.lost_health_from_battle()
                    self.parent.state.disable_health_recovery_today()
                    if self.parent.state.health > 0:
                        self.parent.audio.play(self.parent.audio.VictorySound)
                        infoDialog(self, self.tr("Battle won!"), self.tr("You have defeated the pirate fleet, "
                                                                         "and can continue with your travels."))

                if (not battle_won) or (self.parent.state.health == 0):
                    self.parent.audio.play(self.parent.audio.DeathSound)
                    infoDialog(self, self.tr("Battle lost!"), self.tr("You have been defeated by the pirate fleet."
                                                                      "<br><br>You are dead."))
                    self.parent.checkHighScore()
                    self.parent.reset()
                    return
            else:
                if (self.parent.state.items.count() == 0) or percentChance(20):
                    # take 95-99% percent of players money
                    percent_to_take = random.randint(95, 99)
                    money_to_take = (float(self.parent.state.money) / 100.0) * percent_to_take
                    self.parent.state.money -= int(money_to_take)

                self.parent.state.items.remove_all_items()
                self.parent.playerItemBrowser.update()
                self.parent.updatePlayerItemsLabel()
                self.parent.infoBar.update()

                self.parent.audio.play(self.parent.audio.FailureSound)
                infoDialog(self, self.tr("Surrender"), self.tr("You decide not to fight the pirate fleet. "
                                                               "<br><br>The pirates spare your life, but they "
                                                               "rob you of everything you've got!"))

        self.parent.audio.play(self.parent.audio.TravelSound)
        self.parent.state.change_current_planet(planet)
        self.parent.advanceDay()

        # Every distance in the table has changed
        self.refreshDistances()

    def openTradingConsole(self, planet):
        trading_console = TradingConsole(self.parent, planet)
        trading_console.exec_()

    def pricesButtonClicked(self):
        planet = self.selectedPlanet()
        if planet is None:
            errorDialog(self, message=self.tr("Please select a planet first!"))
            return

        self.openTradingConsole(planet)

    def travelButtonClicked(self):
        planet = self.selectedPlanet()
        if planet is None:
            errorDialog(self, message=self.tr("Please select a planet to travel to first!"))
            return

        self.travelToPlanet(planet)

    def onDoubleClick(self, signal):
        planet = self.selectedPlanet()
        if planet is not None:
            self.travelToPlanet(planet)

    def homeButtonClicked(self):
        home = self.parent.state.home_planet
        self.travelToPlanet(home)

        # If the trip happened, select the home planet in the table (unless the search box hides it)
        if self.parent.state.current_planet is home:
            selectRowByKey(self.table, home)

    def previousButtonClicked(self):
        if self.parent.state.previous_planet is None:
            errorDialog(self, message=self.tr("No previous planet to travel to!"))
            return

        if self.parent.state.previous_planet not in self.parent.state.planets:
            errorDialog(self, message=self.tr("{0} no longer exists!", "{0} is a planet name").format(
                                      self.parent.state.previous_planet.full_name))
            return

        self.travelToPlanet(self.parent.state.previous_planet)
