import copy
import random
from deep_space_trader.utils import errorDialog, infoDialog, yesNoDialog
from deep_space_trader.location_picker import PlanetDestructionPicker
from deep_space_trader import constants as const

from PyQt5 import QtWidgets, QtCore, QtGui


store_items = []


class StoreItem(object):
    def __init__(self, name, description, price):
        self.name = name
        self.description = description
        self.price = price

    def use(self, parent):
        raise NotImplementedError()

    def after_use(self, parent):
        pass


class PlanetExploration(StoreItem):
    def __init__(self):
        price = const.PLANET_EXPLORATION_COST
        name = "Planet discovery expedition"
        desc = (
            "Allows you to mount an expedition to discover new planets"
        )

        super(PlanetExploration, self).__init__(name, desc, price)

    def use(self, parent):
        if len(parent.state.planets) > const.MAX_PLANETS_ALLOWED:
            errorDialog(parent, "Error", "Too many planets, you need to destroy "
                                         "some planets before you can discover more")
            return

        if not yesNoDialog(parent, "Are you sure?",
                           message="Are you sure you want to buy a %s" % self.name):
            return

        num_new = random.randrange(*parent.state.planet_discovery_range)
        parent.state.expand_planets(num_new)

        infoDialog(parent, "%d new planets with intelligent life have "
                         "been discovered!" % num_new)

        parent.infoBar.update()
        parent.locationBrowser.update()
        return True


class PlanetExplorationUpgrade(StoreItem):
    def __init__(self):
        self.range = const.PLANET_DISCOVERY_RANGE
        price = const.PLANET_EXPLORATION_UPGRADE_COST
        name = "Planet discovery upgrade"
        desc = (
            ""
        )

        super(PlanetExplorationUpgrade, self).__init__(name, desc, price)

        self._update_desc()

    def _update_desc(self):
        curr_upper = self.range[1]

        if curr_upper < const.MAX_PLANET_DISCOVERY_RANGE_UPPER:
            max_planets = curr_upper * 2

            desc = (
                "Upgrades your exploration fleet, increasing the max. "
                "number of planets you can discover to %d" % max_planets
            )
        else:
            desc = "You cannot buy this item anymore"

        self.description = desc

    def use(self, parent):
        if self.range[1] >= const.MAX_PLANET_DISCOVERY_RANGE_UPPER:
            errorDialog(parent, "Error", "You cannot expand your planet "
                                         "discovery range any further")
            return

        if not yesNoDialog(parent, "Are you sure?",
                           message="Are you sure you want to buy a %s" % self.name):
            return

        parent.state.planet_discovery_range = (self.range[0] * 2, self.range[1] * 2)
        self.range = parent.state.planet_discovery_range
        infoDialog(parent, "Exploration fleet successfully upgraded")
        return True

    def after_use(self, parent):
        self.price *= 2
        self._update_desc()

class PlanetDestruction(StoreItem):
    def __init__(self):
        price = const.PLANET_DESTRUCTION_COST
        name = "Planet destruction kit"
        desc = (
            "Allows you to destroy a planet and gain all of its resources"
        )

        super(PlanetDestruction, self).__init__(name, desc, price)

    def use(self, parent):
        if len(parent.state.planets) == 1:
            errorDialog(parent, "Error", message="The only planet available is "
                                         "the one you are currently on")
            return

        dialog = PlanetDestructionPicker(parent)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
        return dialog.accepted


class CapacityIncrease(StoreItem):
    def __init__(self):
        self.incr = const.CAPACITY_INCREASE
        price = const.CAPACITY_INCREASE_COST
        name = "Increase item capacity"
        desc = "Doubles your item capacity"

        super(CapacityIncrease, self).__init__(name, desc, price)

    def use(self, parent):
        if not yesNoDialog(parent, "Are you sure?",
                           message="Are you sure want to increase your capacity?"):
            return False

        parent.state.capacity += self.incr
        parent.infoBar.update()
        parent.updatePlayerItemsLabel()
        infoDialog(parent, "Success", message="Capacity successfully increased. "
                                      "New capacity is {:,}".format(parent.state.capacity))

        return True

    def after_use(self, parent):
        self.incr *= 2
        self.price *= 2


class WarehouseSpeedIncrease(StoreItem):
    def __init__(self):
        price = const.WAREHOUSE_SPEED_INCREASE_COST
        name = "Increase warehouse limit"
        desc = (
            "Increases your engine power, allowing you to make one more trip to "
            "the warehouse per day."
        )

        super(WarehouseSpeedIncrease, self).__init__(name, desc, price)

    def use(self, parent):
        if not yesNoDialog(parent, "Are you sure?",
                           message="Are you sure want to increase the warehouse limit?"):
            return False

        parent.state.warehouse_gets_per_day += 1
        parent.state.warehouse_puts_per_day += 1

        return True


def load_store_items():
    store_items.clear()
    store_items.extend([
        CapacityIncrease(),
        PlanetExploration(),
        PlanetExplorationUpgrade(),
        PlanetDestruction(),
        WarehouseSpeedIncrease()
    ])


class Store(QtWidgets.QDialog):
    def __init__(self, parent):
        super(Store, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        buttonLayout = QtWidgets.QHBoxLayout()

        self.buyButton = QtWidgets.QPushButton("Buy item")
        self.buyButton.clicked.connect(self.buyButtonClicked)
        buttonLayout.addWidget(self.buyButton)

        self.moneyLabel = QtWidgets.QLabel()
        self.updateMoneyLabel()
        buttonLayout.addWidget(self.moneyLabel)

        self.mainLayout.addLayout(buttonLayout)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Item', 'description', 'Price'])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setWordWrap(True)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.table.doubleClicked.connect(self.onDoubleClick)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        self.table.resizeRowsToContents()

        self.mainLayout.addWidget(self.table)
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Store")

        self.update()

    def updateMoneyLabel(self):
        self.moneyLabel.setText("Your money: {:,}".format(self.parent.state.money))

    def addRow(self, item):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = QtWidgets.QTableWidgetItem(item.name)
        item2 = QtWidgets.QTableWidgetItem(item.description)
        item3 = QtWidgets.QTableWidgetItem('{:,}'.format(item.price))

        item3.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)
        self.table.setItem(nextFreeRow, 2, item3)

    def populateTable(self):
        self.table.setRowCount(0)
        for item in store_items:
            self.addRow(item)

    def update(self):
        self.populateTable()
        super(Store, self).update()

    def buyItem(self, item):
        if self.parent.state.store_purchases >= self.parent.state.max_store_purchases_per_day:
            errorDialog(self, message="You can only make %d store purchases per day. "
                              "Come back tomorrow." % self.parent.state.max_store_purchases_per_day)
            return

        if self.parent.state.money < item.price:
            errorDialog(self, message="You don't have enough money to buy '%s'" % item.name)
            return

        if not item.use(self.parent):
            return

        self.parent.state.store_purchases += 1
        self.parent.state.money -= item.price
        self.parent.infoBar.update()

        item.after_use(self.parent)
        self.update()

    def onDoubleClick(self, signal):
        item = store_items[signal.row()]
        self.buyItem(item)

    def buyButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select an item first")
            return

        item = store_items[selectedRow]
        self.buyItem(item)

    def sizeHint(self):
        return QtCore.QSize(800, 400)
