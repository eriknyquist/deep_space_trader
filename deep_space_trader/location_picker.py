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

        self.selectButton = QtWidgets.QPushButton("Destroy selected")
        self.selectButton.clicked.connect(self.selectButtonClicked)
        self.buttonLayout.addWidget(self.selectButton)
        self.selectButton.setToolTip("destroy the selected planets")

        self.all_planets_cost = const.PLANET_DESTRUCTION_COST * (len(self.state.planets) - 1)
        self.allButton = QtWidgets.QPushButton()

        text = "Destroy all"
        if self.all_planets_cost > 0:
            text += " (cost {:,})".format(self.all_planets_cost)
        else:
            self.allButton.setEnabled(False)

        self.allButton.setText(text)
        self.allButton.clicked.connect(self.allButtonClicked)
        self.buttonLayout.addWidget(self.allButton)
        self.allButton.setToolTip("destroy all planets except the one you are currently on")

        if self.state.money < self.all_planets_cost:
            self.allButton.setEnabled(False)

        self.table = QtWidgets.QTableWidget()

        # Set alternating row colors, but keep default highlight color...
        default_palette = self.table.palette()
        default_highlight = default_palette.color(QtGui.QPalette.Highlight)
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Highlight, default_highlight)
        self.table.setPalette(palette)

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Planet name', 'Planet value'])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.table)

        self.setWindowTitle("Select a planet to destroy")
        self.setLayout(self.mainLayout)
        self.table.resizeColumnsToContents()
        self.update()

    def onSelectionChanged(self, selected, deselected):
        cost = 0
        for index in self.table.selectionModel().selectedRows():
            cost += const.PLANET_DESTRUCTION_COST

        text = "Destroy selected"

        if cost > 0:
            text += " (cost {:,})".format(cost)

        self.selectButton.setText(text)

    def onDoubleClick(self):
        self.selectButtonClicked()

    def populateTable(self):
        self.table.setUpdatesEnabled(False)
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)

        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.state.planets))

        for row in range(len(self.state.planets)):
            planet = self.state.planets[row]
            item1 = QtWidgets.QTableWidgetItem(planet.full_name)
            item2 = QtWidgets.QTableWidgetItem("yes" if planet.visited else "no")
            item2.setTextAlignment(QtCore.Qt.AlignHCenter)
            self.table.setItem(row, 0, item1)
            self.table.setItem(row, 1, item2)

        self.table.setSortingEnabled(True)
        self.table.blockSignals(False)
        self.table.setUpdatesEnabled(True)

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
        percentage_chance_per_planet = 5.0

        percentage_total_chance = int(min(100.0, percentage_chance_per_planet * len(planets_to_destroy)))

        resistance = (random.uniform(0.0, 100.0) <= percentage_total_chance)

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
            "You must defeat them if you want to continue with the destruction of {0}." +
            "<br><br>If you fight and lose, you will die and the game will be over." +
            "<br><br>If you fight and win, you will destroy this planet and gain its materials, " +
            "but you will lose some health."
            "<br><br>If you choose not to fight, you will not be able to destroy this planet, " +
            "but will continue unscathed."
        ).format(resisting_planet.full_name)

        if self.state.battle_level == 0:
            msg += "<br><br>Since you have no battle fleet, your chances of victory are slim. "

        msg += "<br><br>Do you want to fight?"

        self.parent.audio.play(self.parent.audio.BattleSound)
        proceed = yesNoDialog(self, "Planet is resisting!", msg)
        if not proceed:
            self.parent.audio.play(self.parent.audio.FailureSound)
            infoDialog(self.parent, "Chickened out!",
                       message="You have declined to fight %s. They win, this time." % resisting_planet.full_name)

            # Remove resisting planet from list of planets to destroy
            return [p for p in planets_to_destroy if id(p) != id(resisting_planet)]

        battle_won = self.state.battle_won()
        if battle_won:
            self.parent.audio.play(self.parent.audio.VictorySound)
            self.parent.state.lost_health_from_battle()
            if self.parent.state.health > 0:
                infoDialog(self.parent, "Victory!",
                           message="You have defeated %s!" % resisting_planet.full_name)

        if (not battle_won) or (self.parent.state.health == 0):
            self.parent.audio.play(self.parent.audio.DeathSound)
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

        for planet in planets_to_destroy:
            self.state.warehouse.add_all_items(planet.items)
            index = self.parent.state.planets.index(planet)
            self.parent.state.planets.remove(planet)
            self.parent.locationBrowser.table.removeRow(index)

        self.final_price = self.all_planets_cost

        self.close()

        self.parent.audio.play(self.parent.audio.PlanetDestructionSound)
        infoDialog(self.parent, "Success",
                   message="Destruction of all planets is complete.")

    def selectButtonClicked(self):
        selectedRows = [index.row() for index in self.table.selectionModel().selectedRows()]
        if len(selectedRows) < 1:
            errorDialog(self, message="Please select planets to destroy first!")
            return

        planets = [self.parent.state.planets[row] for row in selectedRows]
        destroyed_desc = ""

        if len(planets) == 1:
            msg = ("Are you sure you want to destroy the planet {0}? {0} will cease to exist, and "
                   "all tradeable items that currrently exist on {0} will be shipped to your "
                   "warehouse.".format(planets[0].full_name))
        elif len(planets) < 6:
            planets_desc = ", ".join(p.full_name for p in planets[:-1]) + " and " + planets[-1].full_name
            msg = ("Are you sure you want to destroy {0}? These planets will cease to exist, and "
                   "all tradeable items that currrently exist on these planets will be shipped to your "
                   "warehouse.".format(planets_desc))
        else:
            msg = ("Are you sure you want to destroy {:,} planets? These planets will cease to exist, and "
                   "all tradeable items that currrently exist on these planets will be shipped to your "
                   "warehouse.".format(len(planets)))


        on_planet = any(self.parent.state.current_planet.full_name == planet.full_name for planet in planets)

        if on_planet:
            msg += ("<br><br>Oh, and you are currently on {0}, so you will "
                   "also die.".format(self.parent.state.current_planet.full_name))

        proceed = yesNoDialog(self, "Are you sure?", message=msg)
        if not proceed:
            return

        planets_to_destroy = self.handlePlanetResistance(planets)
        if not planets_to_destroy:
            return

        for planet in planets_to_destroy:
            self.parent.state.warehouse.add_all_items(planet.items)
            index = self.parent.state.planets.index(planet)
            self.parent.state.planets.remove(planet)
            self.parent.locationBrowser.table.removeRow(index)

        self.accepted = True

        if len(planets_to_destroy) == 1:
            destroyed_desc = planets_to_destroy[0].full_name
        elif len(planets_to_destroy) < 6:
            destroyed_desc = (", ".join(p.full_name for p in planets_to_destroy[:-1]) + " and "
                                        + planets_to_destroy[-1].full_name)
        else:
            destroyed_desc = "{:,} planets".format(len(planets_to_destroy))


        self.parent.audio.play(self.parent.audio.PlanetDestructionSound)
        infoDialog(self.parent, "Success", message="Destruction of %s is complete."
                                                   % destroyed_desc)

        if on_planet:
            self.parent.audio.play(self.parent.audio.DeathSound)
            infoDialog(self.parent, "Dead!", message="You destroyed the planet "
                                                     "you were on, and killed yourself.<br><br>"
                                                     "You are dead.")
            self.died = True

        self.close()

    def sizeHint(self):
        return QtCore.QSize(600, 400)
