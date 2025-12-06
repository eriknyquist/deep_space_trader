import random

from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog
from deep_space_trader.item_browsers import TradingConsolePlanetDisplay

from PyQt5 import QtWidgets, QtCore, QtGui

TRADING_CONSOLE_MESSAGE = ("You must buy the trading console from the store if "
                           "you want to be able to see planet item prices without "
                           "travelling to the planet")


class TradingConsole(QtWidgets.QDialog):
    def __init__(self, parent, planet):
        super(TradingConsole, self).__init__(parent)

        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.addWidget(TradingConsolePlanetDisplay(parent, planet))
        self.setLayout(self.mainLayout)
        self.update()
        self.adjustSize()
        self.setWindowTitle("Item prices on " + planet.full_name)

    def sizeHint(self):
        return QtCore.QSize(600, 400)


class LocationBrowser(QtWidgets.QWidget):
    def __init__(self, parent):
        super(LocationBrowser, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.planetSearchLayout = QtWidgets.QHBoxLayout()
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.planetSearchText = QtWidgets.QLineEdit()
        self.planetSearchText.setPlaceholderText("Search for planets by name...")
        self.planetSearchText.textChanged.connect(self.planetSearchTextChanged)
        self.planetSearchLayout.addWidget(self.planetSearchText)

        self.travelButton = QtWidgets.QPushButton("Travel...")
        self.travelButton.clicked.connect(self.travelButtonClicked)
        self.buttonLayout.addWidget(self.travelButton)

        self.previousButton = QtWidgets.QPushButton("Travel to previous")
        self.previousButton.clicked.connect(self.previousButtonClicked)
        self.buttonLayout.addWidget(self.previousButton)

        self.pricesButton = QtWidgets.QPushButton("Trading console")
        self.pricesButton.clicked.connect(self.pricesButtonClicked)
        self.buttonLayout.addWidget(self.pricesButton)
        self.pricesButton.setEnabled(self.parent.state.have_trading_console)

        self.table = QtWidgets.QTableWidget()

        # Set alternating row colors, but keep default highlight color...
        default_palette = self.table.palette()
        default_highlight = default_palette.color(QtGui.QPalette.Highlight)
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Highlight, default_highlight)
        self.table.setPalette(palette)

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Planet', 'visited?'])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.onDoubleClick)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.mainLayout.addLayout(self.planetSearchLayout)
        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.table)

        self.tradingConsoleTooltip = TRADING_CONSOLE_MESSAGE
        self.tooltipsEnabled = True
        self.setTooltips()
        self.table.resizeColumnsToContents()
        self.update()

    def enableTooltips(self, enabled):
        self.tooltipsEnabled = enabled
        self.setTooltips()

    def setTooltips(self):
        if self.tooltipsEnabled:
            self.travelButton.setToolTip("travel to the selected planet")
            self.previousButton.setToolTip("travel back to the planet you were on before the current planet")
            self.pricesButton.setToolTip(self.tradingConsoleTooltip)
        else:
            self.travelButton.setToolTip(None)
            self.previousButton.setToolTip(None)
            self.pricesButton.setToolTip(None)

    def enableTradingConsole(self):
        self.pricesButton.setEnabled(True)
        self.tradingConsoleTooltip = ("opens the trading console for the selected planet, "
                                      "allowing you to see item prices without travelling there")
        self.pricesButton.setToolTip(self.tradingConsoleTooltip)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Return:
            if self.parent.state.have_trading_console:
                planetname = self.table.item(self.table.currentRow(), 0).text()
                self.openTradingConsole(planetname)
            else:
                errorDialog(self, message=TRADING_CONSOLE_MESSAGE)

    def planetSearchTextChanged(self, newText):
        if not newText.strip():
            self.update()
            return

        text = newText.strip().lower()
        self.table.setRowCount(0)
        for planet in self.parent.state.planets:
            if text in planet.full_name.lower():
                self.addRow(planet)

        super(LocationBrowser, self).update()

    def addRow(self, planet):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = QtWidgets.QTableWidgetItem(planet.full_name)
        item2 = QtWidgets.QTableWidgetItem("yes" if planet.visited else "no")

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)

    def populateTable(self):
        self.table.setRowCount(0)
        for planet in self.parent.state.planets:
            self.addRow(planet)

    def update(self):
        self.populateTable()
        super(LocationBrowser, self).update()

    def travelToPlanet(self, planetname):
        if self.parent.state.current_planet.full_name == planetname:
            errorDialog(self, message="You are already on %s!" % planetname)
            return

        if self.parent.state.money < self.parent.state.travel_cost:
            errorDialog(self, message="You don't have enough money! (%d required)"
                                      % self.parent.state.travel_cost)
            return

        accepted = yesNoDialog(self, "Travel",
                               "Travel to {0}?<br><br>(cost is {1:,}, you have {2:,})".format(
                               planetname, self.parent.state.travel_cost, self.parent.state.money))
        if not accepted:
            return

        self.parent.state.money -= self.parent.state.travel_cost

        if random.randint(0, 100) <= self.parent.state.chance_of_being_robbed_in_transit():
            accepted = yesNoDialog(self, "Attacked by pirates!",
                                   "You have encountered a pirate fleet while travelling " +
                                   "between planets!<br><br>Your battle fleet must defeat them if " +
                                   "you want to continue.<br><br>If you do not fight, then the only other " +
                                   "option is surrender; you will not die, but you may lose some of " +
                                   "your money and resources.<br><br>Do you want to fight?",
                                   cancelable=False)
            if accepted:
                if self.parent.state.battle_won():
                    infoDialog(self, "Battle won!", "You have defeated the pirate fleet, " +
                               "and can continue with your travels.")
                else:
                    infoDialog(self, "Battle lost!", "You have been defeated by the pirate fleet." +
                               "<br><br>You are dead.")
                    self.parent.checkHighScore()
                    self.parent.reset()
                    return
            else:
                if (self.parent.state.items.count() == 0) or (random.randint(0, 100) >= 80):
                    # take 95-99% percent of players money
                    percent_to_take = random.randint(95, 99)
                    money_to_take = (float(self.parent.state.money) / 100.0) * percent_to_take
                    self.parent.state.money -= int(money_to_take)

                self.parent.state.items.remove_all_items()
                self.parent.playerItemBrowser.update()
                self.parent.infoBar.update()

                infoDialog(self, "Surrender", "You decide not to fight the pirate fleet. " +
                           "<br><br>The pirates spare your life, but they rob you of everything you've got!")

        self.parent.audio.play(self.parent.audio.TravelSound)
        self.parent.state.change_current_planet(planetname)
        self.parent.advanceDay()

        currentRow = self.table.currentRow()
        self.update()
        self.table.selectRow(currentRow)

        self.parent.planetItemBrowser.update()
        self.parent.infoBar.update()

    def openTradingConsole(self, planetname):
        planet = self.parent.state.get_planet_by_name(planetname)
        trading_console = TradingConsole(self.parent, planet)
        trading_console.exec_()

    def pricesButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select a planet first!")
            return

        planetname = self.table.item(selectedRow, 0).text()
        self.openTradingConsole(planetname)

    def travelButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select a planet to travel to first!")
            return

        planetname = self.table.item(selectedRow, 0).text()

        self.travelToPlanet(planetname)

    def onDoubleClick(self, signal):
        selectedRow = self.table.currentRow()
        planetname = self.table.item(selectedRow, 0).text()
        self.travelToPlanet(planetname)

    def previousButtonClicked(self):
        if self.parent.state.previous_planet is None:
            errorDialog(self, message="No previous planet to travel to!")
            return

        self.travelToPlanet(self.parent.state.previous_planet.full_name)
