import copy
import random
from deep_space_trader.utils import errorDialog, infoDialog, yesNoDialog, ICON_PATH
from deep_space_trader.location_picker import PlanetDestructionPicker
from deep_space_trader import constants as const

from PyQt5 import QtWidgets, QtCore, QtGui


store_items = []


class StoreItem(object):
    def __init__(self, parent, name, description, price):
        self.died = False
        self.name = name
        self.description = description
        self.price = price
        self.parent = parent

    def use(self):
        raise NotImplementedError()

    def after_use(self):
        pass


class PlanetExploration(StoreItem):
    def __init__(self, parent):
        price = const.PLANET_EXPLORATION_COST
        name = "Scout expedition"
        desc = (
            "Send your planet scouting fleet on an expedition to discover new "
            "planets that you can trade with."
        )

        super(PlanetExploration, self).__init__(parent, name, desc, price)

    def use(self):
        if self.parent.state.scout_level == 0:
            errorDialog(self.parent, "Sorry!", "You need to buy a scout fleet for scout "
                                               "expeditions to be possible")
            return

        if len(self.parent.state.planets) == const.MAX_PLANETS_ALLOWED:
            errorDialog(self.parent, "Sorry!", "Too many planets, you need to destroy "
                                         "some planets before you can discover more")
            return False

        if not yesNoDialog(self.parent, "Are you sure?",
                           message="Are you sure you want to buy a %s?" % self.name):
            return False

        num_new = random.randrange(*self.parent.state.planet_discovery_range)
        if (num_new + len(self.parent.state.planets)) > const.MAX_PLANETS_ALLOWED:
            num_new = const.MAX_PLANETS_ALLOWED - len(self.parent.state.planets)

        self.parent.state.expand_planets(num_new)

        self.parent.audio.play(self.parent.audio.PlanetDiscoverySound)
        infoDialog(self.parent, "%d new planets willing to do business with you have "
                         "been discovered!" % num_new)

        self.parent.infoBar.update()
        self.parent.locationBrowser.update()
        return True


class PlanetDestruction(StoreItem):
    def __init__(self, parent):
        price = const.PLANET_DESTRUCTION_COST
        name = "Planet destruction kit"
        desc = (
            "Destroy planets and transport all of their resources to your warehouse"
        )

        super(PlanetDestruction, self).__init__(parent, name, desc, price)

    def use(self):
        dialog = PlanetDestructionPicker(self.parent, self)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

        if dialog.accepted:
            self.price = dialog.final_price

        self.died = dialog.died
        return dialog.accepted

    def after_use(self):
        self.parent.locationBrowser.update()
        self.parent.warehouseItemBrowser.update()


class CapacityIncrease(StoreItem):
    def __init__(self, parent):
        self.incr = const.CAPACITY_INCREASE
        price = const.CAPACITY_INCREASE_COST
        name = "Increase ship capacity"
        desc = "Double the number of items your ship can hold."

        super(CapacityIncrease, self).__init__(parent, name, desc, price)

    def use(self):
        if not yesNoDialog(self.parent, "Are you sure?",
                           message="Are you sure want to increase your ship's capacity?"):
            return False

        self.parent.audio.play(self.parent.audio.ShipUpgradeSound)
        self.parent.state.capacity += self.incr
        self.parent.infoBar.update()
        self.parent.updatePlayerItemsLabel()
        infoDialog(self.parent, "Success", message="Capacity successfully increased. "
                                      "New capacity is {:,}.".format(self.parent.state.capacity))

        return True

    def after_use(self):
        self.incr *= 2
        self.price *= 2


class ScoutFleetUpgrade(StoreItem):
    def __init__(self, parent):
        self.range = const.PLANET_DISCOVERY_RANGE
        price = const.PLANET_EXPLORATION_UPGRADE_COST
        name = "Buy scout fleet"
        desc = (
            "Buy a planet scouting fleet, allowing you to discover "
            "new planets to trade with. Increases your daily costs by {:,}.".format(const.DAILY_SCOUT_FLEET_COST_PER_LEVEL)
        )

        super(ScoutFleetUpgrade, self).__init__(parent, name, desc, price)

    def _update_desc(self):
        if self.parent.state.scout_level >= self. parent.state.max_scout_level:
            desc = "You cannot buy this item anymore."
            self.price = None
        else:
            max_planets = self.range[1] * 2
            desc = ("Upgrade your planet scouting fleet, increasing the max. "
                    "number of planets you can discover in a single scout expedition to {}. "
                    "Increases your daily costs by {:,}. ".format(max_planets, const.DAILY_SCOUT_FLEET_COST_PER_LEVEL))

        self.name = "Upgrade scout fleet"
        self.description = desc

    def use(self):
        if self.parent.state.scout_level >= self.parent.state.max_scout_level:
            errorDialog(self.parent, "Sorry!", "You cannot upgrade your scout fleet "
                                         "any further")
            return False

        if self.parent.state.scout_level == 0:
            check_desc = "buy a"
            confirm_desc = "purchased"
        else:
            check_desc = "upgrade your"
            confirm_desc = "upgraded"

        if not yesNoDialog(self.parent, "Are you sure?",
                           message="Are you sure you want to %s scout fleet?" % check_desc):
            return False

        if self.parent.state.scout_level > 0:
            self.parent.state.planet_discovery_range = (self.range[0] * 2, self.range[1] * 2)

        self.parent.state.scout_level += 1
        self.parent.state.daily_cost += const.DAILY_SCOUT_FLEET_COST_PER_LEVEL
        self.range = self.parent.state.planet_discovery_range
        self.parent.audio.play(self.parent.audio.ScoutUpgradeSound)
        infoDialog(self.parent, "Scout fleet successfully %s." % confirm_desc)
        return True

    def after_use(self):
        self.price *= 2
        self._update_desc()


class BattleFleetUpgrade(StoreItem):
    def __init__(self, parent):
        self.used = False
        price = const.BATTLE_UPGRADE_COST
        name = "Buy battle fleet"

        self.desc_fmt = ("{} battle fleet. Gives you a better chance of defeating "
                         "pirate fleets, or planets that resist destruction. "
                         "Increases your daily costs by {:,}.")

        desc = self.desc_fmt.format("Buy a", const.DAILY_BATTLE_FLEET_COST_PER_LEVEL)

        super(BattleFleetUpgrade, self).__init__(parent, name, desc, price)

    def use(self):
        if self.used:
            check_str = "upgrade your"
            bought_str = "upgraded"
        else:
            check_str = "buy a"
            bought_str = "purchased"

        if not yesNoDialog(self.parent, "Are you sure?",
                           message="Are you sure want to %s battle fleet?" % check_str):
            return False

        if self.parent.state.battle_level >= self.parent.state.max_battle_level:
            errorDialog(self.parent, "Sorry!", message="You cannot upgrade your battle "
                                                 "fleet anymore.")
            return False

        self.parent.state.battle_level += 1
        self.parent.state.daily_cost += const.DAILY_BATTLE_FLEET_COST_PER_LEVEL

        if not self.used:
            self.used = True
            self.name = "Upgrade battle fleet"
            self.description = self.desc_fmt.format("Upgrades your", const.DAILY_BATTLE_FLEET_COST_PER_LEVEL)

        self.parent.audio.play(self.parent.audio.BattleUpgradeSound)
        infoDialog(self.parent, "Success", message="Battle fleet successfully %s." % bought_str)

        return True

    def after_use(self):
        if self.parent.state.battle_level >= self.parent.state.max_battle_level:
            self.description = "You cannot buy this item anymore."
            self.price = None
        else:
            self.price *= 2


class WarehouseSpeedIncrease(StoreItem):
    def __init__(self, parent):
        price = const.WAREHOUSE_SPEED_INCREASE_COST
        name = "Increase max. warehouse trips per day"
        desc = (
            "Increase your engine power, allowing you to make two more trips to "
            "the warehouse per day."
        )

        super(WarehouseSpeedIncrease, self).__init__(parent, name, desc, price)

    def use(self):
        if not yesNoDialog(self.parent, "Are you sure?",
                           message="Are you sure want to increase max. number of "
                                   "warehouse trips per day?"):
            return False

        self.parent.state.warehouse_trips_per_day += 2

        self.parent.audio.play(self.parent.audio.WarehouseTripsUpgradeSound)
        infoDialog(self.parent, "Success", message="Max. warehouse trips per day successfully increased.")

        return True

class TradingConsole(StoreItem):
    def __init__(self, parent):
        price = const.TRADING_CONSOLE_COST
        name = "Trading console"
        desc = (
            "Allows you to view current item prices on any planet without travelling. "
            "Increases your daily costs by {:,}.".format(const.DAILY_TRADING_CONSOLE_COST)
        )

        super(TradingConsole, self).__init__(parent, name, desc, price)

    def use(self):
        if not yesNoDialog(self.parent, "Are you sure?",
                           message="Are you sure want to buy the trading console?"):
            return False

        self.parent.state.enable_trading_console()
        self.parent.state.daily_cost += const.DAILY_TRADING_CONSOLE_COST
        self.parent.audio.play(self.parent.audio.TradingConsoleSound)
        infoDialog(self.parent, "Success", message="Trading console successfully purchased")

        return True

    def after_use(self):
        self.description = "You have already purchased this item."
        self.price = None


def load_store_items(parent):
    store_items.clear()
    store_items.extend([
        CapacityIncrease(parent),
        PlanetExploration(parent),
        PlanetDestruction(parent),
        ScoutFleetUpgrade(parent),
        BattleFleetUpgrade(parent),
        WarehouseSpeedIncrease(parent),
        TradingConsole(parent)
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

        # Set alternating row colors, but keep default highlight color...
        default_palette = self.table.palette()
        default_highlight = default_palette.color(QtGui.QPalette.Highlight)
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Highlight, default_highlight)
        self.table.setPalette(palette)

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
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        self.update()

    def updateMoneyLabel(self):
        self.moneyLabel.setText("Your money: {:,}".format(self.parent.state.money))

    def addRow(self, item):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        price = "N/A" if item.price is None else '{:,}'.format(item.price)

        item1 = QtWidgets.QTableWidgetItem(item.name)
        item2 = QtWidgets.QTableWidgetItem(item.description)
        item3 = QtWidgets.QTableWidgetItem(price)

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
            errorDialog(self, "Sorry!", "You can only make %d store purchases per day. "
                              "Come back tomorrow." % self.parent.state.max_store_purchases_per_day)
            return

        if item.price is None:
            errorDialog(self, "Sorry!", "You cannot buy this item anymore")
            return

        if self.parent.state.money < item.price:
            errorDialog(self, "Sorry!", "You don't have enough money to buy '%s'" % item.name)
            return

        proceed = item.use()

        if item.died:
            self.parent.checkHighScore()
            self.parent.reset()
            self.close()
            return

        if not proceed:
            return

        self.parent.state.store_purchases += 1
        self.parent.state.money -= item.price
        self.parent.infoBar.update()

        item.after_use()
        self.update()

    def onDoubleClick(self, signal):
        item = store_items[signal.row()]
        self.buyItem(item)

    def buyButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, "Oops!", "Please select an item first")
            return

        item = store_items[selectedRow]
        self.buyItem(item)

    def sizeHint(self):
        return QtCore.QSize(800, 400)
