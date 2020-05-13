from deep_space_trader import constants as const
from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog

from PyQt5 import QtWidgets, QtCore, QtGui


class PlanetDestructionPicker(QtWidgets.QDialog):
    def __init__(self, parent):
        super(PlanetDestructionPicker, self).__init__(parent)

        self.accepted = False
        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.selectButton = QtWidgets.QPushButton("Destroy")
        self.selectButton.clicked.connect(self.selectButtonClicked)
        self.buttonLayout.addWidget(self.selectButton)

        self.all_planets_cost = const.PLANET_DESTRUCTION_COST * (len(parent.state.planets) - 1)
        self.allButton = QtWidgets.QPushButton("Destroy all (cost {:,})".format(self.all_planets_cost))
        self.allButton.clicked.connect(self.allButtonClicked)
        self.buttonLayout.addWidget(self.allButton)

        if parent.state.money < self.all_planets_cost:
            self.allButton.setEnabled(False)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(['Discovered planets'])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.onDoubleClick)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.table)

        self.setWindowTitle("Select a planet to destroy")
        self.setLayout(self.mainLayout)
        self.table.resizeColumnsToContents()
        self.update()

    def onDoubleClick(self):
        self.selectButtonClicked()

    def addRow(self, planet):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = QtWidgets.QTableWidgetItem(planet.full_name)
        item1.setTextAlignment(QtCore.Qt.AlignHCenter)
        self.table.setItem(nextFreeRow, 0, item1)

    def populateTable(self):
        self.table.setRowCount(0)
        for planet in self.parent.state.planets:
            self.addRow(planet)

    def update(self):
        self.populateTable()
        super(PlanetDestructionPicker, self).update()

    def allButtonClicked(self):
        proceed = yesNoDialog(self, "Are you sure?",
                              message="Are you sure you want to destroy all planets? "
                                      "All planets except for the one you are currently "
                                      "on will cease to exist, and all tradeable items "
                                      "that currrently exist on those planets will be "
                                      "shipped to your warehouse.")
        if not proceed:
            return

        for planet in self.parent.state.planets:
            if planet.full_name == self.parent.state.current_planet.full_name:
                continue

            self.parent.state.warehouse.add_all_items(planet.items)

        self.parent.state.planets = [self.parent.state.current_planet]
        self.parent.state.money -= self.all_planets_cost

        self.parent.infoBar.update()
        self.parent.locationBrowser.update()
        self.parent.warehouseItemBrowser.update()
        self.parent.infoBar.update()
        self.close()

        # Set this to false so the money doesn't get updated, we're updating
        # the money here instead
        self.accepted = False

        infoDialog(self.parent, "Success",
                   message="Your destruction of all planets is complete.")

    def selectButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select a planet to travel to first!")
            return

        planet = self.parent.state.planets[selectedRow]

        if self.parent.state.current_planet.full_name == planet.full_name:
            errorDialog(self, message="You are currently on %s, you cannot "
                                      "destroy a planet that you are on" %
                                      planet.full_name)
            return

        proceed = yesNoDialog(self, "Are you sure?",
                              message="Are you sure you want to destroy the "
                                      "planet {0}? {0} will cease to exist, and "
                                      "all tradeable items that currrently exist "
                                      "on {0} will be shipped to your "
                                      "warehouse.".format(planet.full_name))
        if not proceed:
            return

        self.parent.state.warehouse.add_all_items(planet.items)
        del self.parent.state.planets[selectedRow]

        self.parent.infoBar.update()
        self.parent.locationBrowser.update()
        self.parent.warehouseItemBrowser.update()
        self.parent.infoBar.update()
        self.close()
        self.accepted = True

        infoDialog(self.parent, "Success", message="Your destruction of %s is complete."
                                                   % planet.full_name)

    def sizeHint(self):
        return QtCore.QSize(600, 400)
