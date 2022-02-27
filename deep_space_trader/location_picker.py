import random
from deep_space_trader import constants as const
from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog

from PyQt5 import QtWidgets, QtCore, QtGui


class PlanetDestructionPicker(QtWidgets.QDialog):
    def __init__(self, parent, store_item):
        super(PlanetDestructionPicker, self).__init__(parent)

        self.died = False
        self.state = parent.state
        self.final_price = store_item.price
        self.accepted = False
        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.selectButton = QtWidgets.QPushButton("Destroy")
        self.selectButton.clicked.connect(self.selectButtonClicked)
        self.buttonLayout.addWidget(self.selectButton)

        self.all_planets_cost = const.PLANET_DESTRUCTION_COST * (len(self.state.planets) - 1)
        self.allButton = QtWidgets.QPushButton("Destroy all (cost {:,})".format(self.all_planets_cost))
        self.allButton.clicked.connect(self.allButtonClicked)
        self.buttonLayout.addWidget(self.allButton)

        if self.state.money < self.all_planets_cost:
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
        for planet in self.state.planets:
            self.addRow(planet)

    def update(self):
        self.populateTable()
        super(PlanetDestructionPicker, self).update()

    def checkForResistingPlanet(self, planets_to_destroy):
        # First, see if the list of planets to destroy contains a planet that
        # has already resisted destruction; it would make sense for them to resist again,
        # so if such a planet exists then it should resist again now
        for p in planets_to_destroy:
            if p.resists_destruction:
                return p

        # Otherwise, just calculate a numerical percentage representing the chance
        # That one of the planets in the list would resist. There is a 0.005% chance
        # that any single planet will be able to resist us and possibly stop us from destroying it.
        percentage_chance_per_planet = 0.05

        percentage_total_chance = int(max(1.0, percentage_chance_per_planet * len(planets_to_destroy)))

        resistance = (random.randint(0, 100) <= percentage_total_chance)

        if resistance:
            return random.choice(planets_to_destroy)

        # No resistance
        return None

    def handlePlanetResistance(self, planets_to_destroy):
        successful = True
        resisting_planet = self.checkForResistingPlanet(planets_to_destroy)
        if resisting_planet is None:
            return planets_to_destroy

        resisting_planet.resists_destruction = True

        msg = (
            "Planet {0} is resisting destruction! A battle fleet from {0} has been " +
            "dispatched, and is prepared to defend the planet if you try to destroy it. " +
            "You must defeat them if you want to continue with the destruction of {0}. "
        ).format(resisting_planet.full_name)

        if self.state.battle_level == 0:
            msg += "<br><br>Since you have no battle fleet, your chances of victory are slim. "

        msg += "<br><br>Do you want to fight?"

        proceed = yesNoDialog(self, "Planet is resisting!", msg)
        if not proceed:
            infoDialog(self.parent, "Chickened out!",
                       message="You have declined to fight %s. They win, this time." % resisting_planet.full_name)

            # Remove resisting planet from list of planets to destroy
            return [p for p in planets_to_destroy if id(p) != id(resisting_planet)]

        if self.state.battle_won():
            infoDialog(self.parent, "Victory!",
                       message="You have defeated %s!" % resisting_planet.full_name)
        else:
            infoDialog(self.parent, "Defeat!",
                       message="You have been defeated in battle by %s."
                               "<br><br><br>You are dead :(" % resisting_planet.full_name)
            planets_to_destroy = None
            self.died = True
            self.close()
            return []

        return planets_to_destroy

    def allButtonClicked(self):
        proceed = yesNoDialog(self, "Are you sure?",
                              message="Are you sure you want to destroy all planets for {0:,}? "
                                      "All planets except for the one you are currently "
                                      "on will cease to exist, and all tradeable items "
                                      "that currrently exist on those planets will be "
                                      "shipped to your warehouse.".format(self.all_planets_cost))
        if not proceed:
            return

        self.accepted = True
        planets_to_destroy = [p for p in self.state.planets if id(p) != id(self.state.current_planet)]

        planets_to_destroy = self.handlePlanetResistance(planets_to_destroy)
        if not planets_to_destroy:
            return

        for p in planets_to_destroy:
            self.state.warehouse.add_all_items(p.items)

        self.state.planets = [p for p in self.state.planets if p not in planets_to_destroy]
        self.final_price = self.all_planets_cost

        self.close()

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

        if not self.handlePlanetResistance([planet]):
            return

        self.parent.state.warehouse.add_all_items(planet.items)
        del self.parent.state.planets[selectedRow]

        self.close()
        self.accepted = True

        infoDialog(self.parent, "Success", message="Your destruction of %s is complete."
                                                   % planet.full_name)

    def sizeHint(self):
        return QtCore.QSize(600, 400)
