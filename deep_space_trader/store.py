import random
from deep_space_trader.utils import errorDialog, infoDialog, yesNoDialog, ICON_PATH
from deep_space_trader.location_picker import PlanetDestructionPicker
from deep_space_trader import constants as const
from deep_space_trader.i18n import translate, formatNumber, formatPercent

from PyQt5 import QtWidgets, QtCore, QtGui


store_items = []


class StoreItem(object):
    def __init__(self, parent, name, description, price):
        self.died = False
        self.name = name
        self.description = description
        self.price = price
        self.parent = parent
        self.final_price = None

    def use(self):
        raise NotImplementedError()

    def after_use(self):
        pass


class PlanetExploration(StoreItem):
    def __init__(self, parent):
        price = const.PLANET_EXPLORATION_COST
        name = translate("PlanetExploration", "Scout expedition")
        desc = translate("PlanetExploration",
            "Send your planet scouting fleet on an expedition to discover new "
            "planets that you can trade with."
        )

        super(PlanetExploration, self).__init__(parent, name, desc, price)

    def use(self):
        if self.parent.state.scout_level == 0:
            errorDialog(self.parent, translate("PlanetExploration", "Sorry!"),
                        translate("PlanetExploration", "You need to buy a scout fleet for scout "
                                                       "expeditions to be possible"))
            return

        if len(self.parent.state.planets) == const.MAX_PLANETS_ALLOWED:
            errorDialog(self.parent, translate("PlanetExploration", "Sorry!"),
                        translate("PlanetExploration", "Too many planets, you need to destroy "
                                                       "some planets before you can discover more"))
            return False

        if not yesNoDialog(self.parent, translate("PlanetExploration", "Are you sure?"),
                           message=translate("PlanetExploration",
                                             "Are you sure you want to buy a scout expedition?")):
            return False

        num_new = random.randint(*self.parent.state.planet_discovery_range)
        if (num_new + len(self.parent.state.planets)) > const.MAX_PLANETS_ALLOWED:
            num_new = const.MAX_PLANETS_ALLOWED - len(self.parent.state.planets)

        self.parent.state.expand_planets(num_new)
        self.parent.infoBar.update()
        self.parent.locationBrowser.update()

        self.parent.audio.play(self.parent.audio.PlanetDiscoverySound)
        infoDialog(self.parent, translate("PlanetExploration",
                                          "%Ln new planets willing to do business with you have "
                                          "been discovered!", None, num_new))

        return True


class PlanetDestruction(StoreItem):
    def __init__(self, parent):
        price = const.PLANET_DESTRUCTION_COST
        name = translate("PlanetDestruction", "Planet destruction kit")
        desc = translate("PlanetDestruction",
            "Destroy planets and transport all of their resources to your warehouse"
        )

        super(PlanetDestruction, self).__init__(parent, name, desc, price)

    def use(self):
        dialog = PlanetDestructionPicker(self.parent, self)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

        if dialog.accepted:
            self.final_price = dialog.final_price

        self.died = dialog.died
        return dialog.accepted

    def after_use(self):
        self.parent.updatePlanetsGroupBoxTitle()
        self.parent.warehouseItemBrowser.update()


class CapacityIncrease(StoreItem):
    def __init__(self, parent):
        self.incr = const.CAPACITY_INCREASE
        price = const.CAPACITY_INCREASE_COST
        name = translate("CapacityIncrease", "Increase ship capacity")
        desc = translate("CapacityIncrease", "Double the number of items your ship can hold.")

        super(CapacityIncrease, self).__init__(parent, name, desc, price)

    def use(self):
        if not yesNoDialog(self.parent, translate("CapacityIncrease", "Are you sure?"),
                           message=translate("CapacityIncrease",
                                             "Are you sure you want to increase your ship's capacity?")):
            return False

        self.parent.audio.play(self.parent.audio.ShipUpgradeSound)
        self.parent.state.capacity += self.incr
        self.parent.infoBar.update()
        self.parent.updatePlayerItemsLabel()
        infoDialog(self.parent, translate("CapacityIncrease", "Success"),
                   message=translate("CapacityIncrease", "Capacity successfully increased. "
                                     "New capacity is {0}.").format(formatNumber(self.parent.state.capacity)))

        return True

    def after_use(self):
        self.incr *= 2
        self.price *= 2


class ScoutFleetUpgrade(StoreItem):
    def __init__(self, parent):
        self.range = const.PLANET_DISCOVERY_RANGE
        price = const.PLANET_EXPLORATION_UPGRADE_COST
        name = translate("ScoutFleetUpgrade", "Buy scout fleet")
        desc = translate("ScoutFleetUpgrade",
            "Buy a planet scouting fleet, allowing you to discover "
            "new planets to trade with. Increases your daily costs by {0}."
        ).format(formatNumber(const.DAILY_SCOUT_FLEET_COST_PER_LEVEL))

        super(ScoutFleetUpgrade, self).__init__(parent, name, desc, price)

    def _update_desc(self):
        if self.parent.state.scout_level >= self. parent.state.max_scout_level:
            desc = translate("ScoutFleetUpgrade", "You cannot buy this item anymore.")
            self.price = None
        else:
            max_planets = self.range[1] * 2
            desc = translate("ScoutFleetUpgrade",
                "Upgrade your planet scouting fleet, increasing the max. "
                "number of planets you can discover in a single scout expedition to {0}. "
                "Increases your daily costs by {1}. "
            ).format(formatNumber(max_planets), formatNumber(const.DAILY_SCOUT_FLEET_COST_PER_LEVEL))

        self.name = translate("ScoutFleetUpgrade", "Upgrade scout fleet")
        self.description = desc

    def use(self):
        if self.parent.state.scout_level >= self.parent.state.max_scout_level:
            errorDialog(self.parent, translate("ScoutFleetUpgrade", "Sorry!"),
                        translate("ScoutFleetUpgrade", "You cannot upgrade your scout fleet "
                                                       "any further"))
            return False

        if self.parent.state.scout_level == 0:
            check_msg = translate("ScoutFleetUpgrade", "Are you sure you want to buy a scout fleet?")
            confirm_msg = translate("ScoutFleetUpgrade", "Scout fleet successfully purchased.")
        else:
            check_msg = translate("ScoutFleetUpgrade", "Are you sure you want to upgrade your scout fleet?")
            confirm_msg = translate("ScoutFleetUpgrade", "Scout fleet successfully upgraded.")

        if not yesNoDialog(self.parent, translate("ScoutFleetUpgrade", "Are you sure?"),
                           message=check_msg):
            return False

        if self.parent.state.scout_level > 0:
            self.parent.state.planet_discovery_range = (self.range[0] * 2, self.range[1] * 2)

        self.parent.state.scout_level += 1
        self.parent.state.daily_cost += const.DAILY_SCOUT_FLEET_COST_PER_LEVEL
        self.range = self.parent.state.planet_discovery_range
        self.parent.audio.play(self.parent.audio.ScoutUpgradeSound)
        infoDialog(self.parent, confirm_msg)
        return True

    def after_use(self):
        self.price *= 2
        self._update_desc()


class BattleFleetUpgrade(StoreItem):
    def __init__(self, parent):
        self.used = False
        price = const.BATTLE_UPGRADE_COST
        name = translate("BattleFleetUpgrade", "Buy battle fleet")
        desc = translate("BattleFleetUpgrade",
            "Buy a battle fleet. Gives you a better chance of defeating "
            "pirate fleets, or planets that resist destruction. "
            "Increases your daily costs by {0}."
        ).format(formatNumber(const.DAILY_BATTLE_FLEET_COST_PER_LEVEL))

        super(BattleFleetUpgrade, self).__init__(parent, name, desc, price)

    def use(self):
        if self.used:
            check_msg = translate("BattleFleetUpgrade", "Are you sure you want to upgrade your battle fleet?")
            bought_msg = translate("BattleFleetUpgrade", "Battle fleet successfully upgraded.")
        else:
            check_msg = translate("BattleFleetUpgrade", "Are you sure you want to buy a battle fleet?")
            bought_msg = translate("BattleFleetUpgrade", "Battle fleet successfully purchased.")

        if not yesNoDialog(self.parent, translate("BattleFleetUpgrade", "Are you sure?"),
                           message=check_msg):
            return False

        if self.parent.state.battle_level >= self.parent.state.max_battle_level:
            errorDialog(self.parent, translate("BattleFleetUpgrade", "Sorry!"),
                        message=translate("BattleFleetUpgrade", "You cannot upgrade your battle "
                                                                "fleet anymore."))
            return False

        self.parent.state.battle_level += 1
        self.parent.state.daily_cost += const.DAILY_BATTLE_FLEET_COST_PER_LEVEL

        if not self.used:
            self.used = True
            self.name = translate("BattleFleetUpgrade", "Upgrade battle fleet")
            self.description = translate("BattleFleetUpgrade",
                "Upgrades your battle fleet. Gives you a better chance of defeating "
                "pirate fleets, or planets that resist destruction. "
                "Increases your daily costs by {0}."
            ).format(formatNumber(const.DAILY_BATTLE_FLEET_COST_PER_LEVEL))

        self.parent.audio.play(self.parent.audio.BattleUpgradeSound)
        infoDialog(self.parent, translate("BattleFleetUpgrade", "Success"), message=bought_msg)

        return True

    def after_use(self):
        if self.parent.state.battle_level >= self.parent.state.max_battle_level:
            self.description = translate("BattleFleetUpgrade", "You cannot buy this item anymore.")
            self.price = None
        else:
            self.price *= 2


class EngineUpgrade(StoreItem):
    def __init__(self, parent):
        price = const.WAREHOUSE_SPEED_INCREASE_COST
        name = translate("EngineUpgrade", "Increase engine power")
        desc = translate("EngineUpgrade",
            "Increase your engine power, allowing you to make two more trips to the warehouse "
            "per day, and making travel {0} cheaper per light-year."
        ).format(formatPercent((1.0 - const.ENGINE_TRAVEL_COST_FACTOR) * 100.0))

        super(EngineUpgrade, self).__init__(parent, name, desc, price)

    def use(self):
        if self.parent.state.engine_level >= const.MAX_ENGINE_LEVEL:
            errorDialog(self.parent, translate("EngineUpgrade", "Sorry!"),
                        translate("EngineUpgrade", "Your engines are already at full power."))
            return False

        if not yesNoDialog(self.parent, translate("EngineUpgrade", "Are you sure?"),
                           message=translate("EngineUpgrade", "Are you sure you want to increase your engine power?")):
            return False

        self.parent.state.warehouse_trips_per_day += 2
        self.parent.state.engine_level += 1

        self.parent.audio.play(self.parent.audio.WarehouseTripsUpgradeSound)
        infoDialog(self.parent, translate("EngineUpgrade", "Success"),
                   message=translate("EngineUpgrade", "Engine power successfully increased."))

        return True

    def after_use(self):
        if self.parent.state.engine_level >= const.MAX_ENGINE_LEVEL:
            self.description = translate("EngineUpgrade", "You cannot buy this item anymore.")
            self.price = None

class TradingConsole(StoreItem):
    def __init__(self, parent):
        price = const.TRADING_CONSOLE_COST
        name = translate("TradingConsoleItem", "Trading console")
        desc = translate("TradingConsoleItem",
            "Allows you to view current item prices on any planet without travelling. "
            "Increases your daily costs by {0}."
        ).format(formatNumber(const.DAILY_TRADING_CONSOLE_COST))

        super(TradingConsole, self).__init__(parent, name, desc, price)

    def use(self):
        if not yesNoDialog(self.parent, translate("TradingConsoleItem", "Are you sure?"),
                           message=translate("TradingConsoleItem",
                                             "Are you sure you want to buy the trading console?")):
            return False

        self.parent.state.enable_trading_console()
        self.parent.state.daily_cost += const.DAILY_TRADING_CONSOLE_COST
        self.parent.audio.play(self.parent.audio.TradingConsoleSound)
        infoDialog(self.parent, translate("TradingConsoleItem", "Success"),
                   message=translate("TradingConsoleItem", "Trading console successfully purchased"))

        return True

    def after_use(self):
        self.description = translate("TradingConsoleItem", "You have already purchased this item.")
        self.price = None


def load_store_items(parent):
    store_items.clear()
    store_items.extend([
        CapacityIncrease(parent),
        PlanetExploration(parent),
        PlanetDestruction(parent),
        ScoutFleetUpgrade(parent),
        BattleFleetUpgrade(parent),
        EngineUpgrade(parent),
        TradingConsole(parent)
    ])


class Store(QtWidgets.QDialog):
    def __init__(self, parent):
        super(Store, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        buttonLayout = QtWidgets.QHBoxLayout()

        self.buyButton = QtWidgets.QPushButton(self.tr("Buy item"))
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
        self.table.setHorizontalHeaderLabels([self.tr('Item'), self.tr('description'), self.tr('Price')])
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
        self.setWindowTitle(self.tr("Store"))
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        self.update()

    def updateMoneyLabel(self):
        self.moneyLabel.setText(self.tr("Your money: {0}").format(formatNumber(self.parent.state.money)))

    def addRow(self, item):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        price = self.tr("N/A") if item.price is None else formatNumber(item.price)

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
            # (Counts passed to translate() must be plain variables, or pylupdate5 skips the string)
            max_purchases = self.parent.state.max_store_purchases_per_day
            errorDialog(self, self.tr("Sorry!"),
                        translate("Store", "You can only make %Ln store purchases per day. "
                                           "Come back tomorrow.", None, max_purchases))
            return

        if item.price is None:
            errorDialog(self, self.tr("Sorry!"), self.tr("You cannot buy this item anymore"))
            return

        if self.parent.state.money < item.price:
            errorDialog(self, self.tr("Sorry!"), self.tr("You don't have enough money to buy '{0}'",
                                                         "{0} is the name of a store item").format(item.name))
            return

        proceed = item.use()

        if not proceed:
            return

        if item.final_price is not None:
            price = item.final_price
            item.final_price = None
        else:
            price = item.price

        self.parent.state.store_purchases += 1
        self.parent.state.money -= price
        self.parent.infoBar.update()
        self.updateMoneyLabel()

        if item.died:
            self.parent.checkHighScore()
            self.parent.reset()
            self.close()
            return

        item.after_use()
        self.update()

    def onDoubleClick(self, signal):
        item = store_items[signal.row()]
        self.buyItem(item)

    def buyButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, self.tr("Oops!"), self.tr("Please select an item first"))
            return

        item = store_items[selectedRow]
        self.buyItem(item)

    def sizeHint(self):
        return QtCore.QSize(800, 400)
