from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog

from PyQt5 import QtWidgets, QtCore, QtGui


class LocationBrowser(QtWidgets.QWidget):
    def __init__(self, parent):
        super(LocationBrowser, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.travelButton = QtWidgets.QPushButton("Travel...")
        self.travelButton.clicked.connect(self.travelButtonClicked)
        self.buttonLayout.addWidget(self.travelButton)

        self.previousButton = QtWidgets.QPushButton("Travel to previous")
        self.previousButton.clicked.connect(self.previousButtonClicked)
        self.buttonLayout.addWidget(self.previousButton)

        self.table = QtWidgets.QTableWidget()
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

        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.table)

        self.table.resizeColumnsToContents()
        self.update()

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

        accepted = yesNoDialog(self, "Travel", "Travel to %s? (cost is %d, you have %d)" %
                                               (planetname, self.parent.state.travel_cost,
                                                self.parent.state.money))
        if not accepted:
            return

        self.parent.state.money -= self.parent.state.travel_cost
        self.parent.state.change_current_planet(planetname)
        self.parent.advanceDay()

        currentRow = self.table.currentRow()
        self.update()
        self.table.selectRow(currentRow)

        self.parent.planetItemBrowser.update()
        self.parent.infoBar.update()


    def travelButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select a planet to travel to first!")
            return

        planetname = self.table.item(selectedRow, 0).text()

        self.travelToPlanet(planetname)

    def onDoubleClick(self, signal):
        planet = self.parent.state.planets[signal.row()]
        self.travelToPlanet(planet.full_name)

    def previousButtonClicked(self):
        if self.parent.state.previous_planet is None:
            errorDialog(self, message="No previous planet to travel to!")
            return

        self.travelToPlanet(self.parent.state.previous_planet.full_name)
