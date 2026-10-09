import random

from deep_space_trader.transaction_dialogs import (
        Buy, Sell, PlayerToWarehouse, WarehouseToPlayer, DumpWarehouseItem,
        DumpPlayerItem
)

from deep_space_trader.price_graph import PriceHistoryGraph
from deep_space_trader import constants as const
from deep_space_trader.utils import (
    errorDialog, yesNoDialog, infoDialog, checkForMoneyBonus, selectedRowKey, selectRowByKey
)
from deep_space_trader.items import itemDisplayName
from deep_space_trader.i18n import translate, formatNumber, formatPercent

from PyQt5 import QtWidgets, QtCore, QtGui


class SortableTableWidgetItem(QtWidgets.QTableWidgetItem):
    """
    Abstract class for a QTableWidget that allows custom sorting behaviour
    by allowing a new method, valueToCompare, to be defined that returns the
    value to use for comparison while sorting
    """
    def valueToCompare(self):
        raise NotImplementedError()

    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            try:
                this_value = self.valueToCompare()
                other_value = other.valueToCompare()
            except ValueError:
                pass
            else:
                return this_value < other_value

        return super(SortableTableWidgetItem, self).__lt__(other)

class TableWidgetNumber(SortableTableWidgetItem):
    """
    Sortable QTableWidgetItem for cells containing a number. Shows the number
    formatted for the current locale (or the given text), and sorts by the number
    itself, since the formatted text can't be parsed back reliably in every locale
    """
    def __init__(self, value, text=None):
        super(TableWidgetNumber, self).__init__(formatNumber(value) if text is None else text)
        self.value = value

    def valueToCompare(self):
        return self.value


def itemNameCell(itemname):
    """
    Table cell showing the translated name of an item type, with the item type
    name stored as the row's key (see utils.rowKey)
    """
    cell = QtWidgets.QTableWidgetItem(itemDisplayName(itemname))
    cell.setData(QtCore.Qt.UserRole, itemname)
    return cell


def selectedItemName(table):
    """
    Item type name of the selected row, or None if no row is selected
    """
    return selectedRowKey(table)


def atWarehouse(browser):
    """
    True if the player is on their home planet, where the warehouse is. If not,
    shows an error saying where the warehouse is, and returns False
    """
    state = browser.parent.state
    if state.current_planet is state.home_planet:
        return True

    errorDialog(browser, translate("ItemBrowser", "Warehouse"),
                message=translate("ItemBrowser", "Your warehouse is on {0}. Travel there to use it.",
                                  "{0} is a planet name").format(state.home_planet.full_name))
    return False


class ItemBrowser(QtWidgets.QWidget):
    def __init__(self, parent):
        super(ItemBrowser, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.table = QtWidgets.QTableWidget()

        # Set alternating row colors, but keep default highlight color...
        default_palette = self.table.palette()
        default_highlight = default_palette.color(QtGui.QPalette.Highlight)
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Highlight, default_highlight)
        self.table.setPalette(palette)

        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        self.setupHeader()
        self.populateTable()
        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.table)

        self.buttons = []
        self.tooltipsEnabled = True

        self.table.resizeColumnsToContents()
        self.update()

    def enableTooltips(self, enabled):
        self.tooltipsEnabled = enabled
        self.setTooltips()

    def setTooltips(self):
        if self.tooltipsEnabled:
            for button, tooltip in self.buttons:
                button.setToolTip(tooltip)
        else:
            for button, _ in self.buttons:
                button.setToolTip(None)

    def setupHeader(self):
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([translate("ItemBrowser", 'Item type'),
                                              translate("ItemBrowser", 'Quantity')])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

    def update(self):
        selectedKey = selectedRowKey(self.table)
        self.table.setSortingEnabled(False)
        self.populateTable()
        self.table.setSortingEnabled(True)
        selectRowByKey(self.table, selectedKey)
        super(ItemBrowser, self).update()

    def add_button(self, text, on_click, tooltip):
        b = QtWidgets.QPushButton(text)
        b.clicked.connect(on_click)
        b.setToolTip(tooltip)
        self.buttonLayout.addWidget(b)
        self.buttons.append([b, tooltip])

    def addRow(self, itemname):
        raise NotImplementedError()

    def populateTable(self):
        raise NotImplementedError()


class PlayerItemBrowser(ItemBrowser):
    def __init__(self,  *args, **kwargs):
        super(PlayerItemBrowser, self).__init__(*args, **kwargs)

        self.add_button(self.tr("Sell items"), self.sellButtonClicked,
                        self.tr("sell one or more of the selected item to the current planet"))
        self.add_button(self.tr("Sell all"), self.sellAllButtonClicked,
                        self.tr("sell all items on your ship to the current planet"))
        self.add_button(self.tr("To warehouse"), self.warehouseButtonClicked,
                        self.tr("move one or more of the selected item from your ship to the warehouse"))
        self.add_button(self.tr("Dump"), self.dumpButtonClicked,
                        self.tr("dump one or more of the selected item from your ship"))
        self.add_button(self.tr("Dump all"), self.dumpAllButtonClicked, self.tr("dump all items from your ship"))

        self.table.doubleClicked.connect(self.onDoubleClick)

    def onDoubleClick(self, signal):
        self.sellButtonClicked()

    def introduceNewItem(self, itemname):
        quantity = self.parent.state.items.items[itemname].quantity
        rand_quantity = random.randrange(*const.ITEM_SAMPLE_QUANTITY_RANGE)
        planet = self.parent.state.current_planet

        if quantity <= rand_quantity:
            rand_quantity = max(1, int(quantity / 2))

        msg = translate("PlayerItemBrowser",
                        "{0} has never been seen on {1}, and you will have to persuade them "
                        "that it is worth buying. If you provide a free sample of %Ln {0}, "
                        "this may help your cause.<br><br>Provide a free sample of "
                        "%Ln {0}?", "{0} is an item name, e.g. tin, and {1} is a planet name",
                        rand_quantity).format(itemDisplayName(itemname), planet.full_name)

        proceed = yesNoDialog(self, self.tr("Provide sample?"), message=msg)
        if not proceed:
            return

        if itemname in planet.samples_today:
            errorDialog(self, self.tr("Already sampled today"),
                        message=self.tr("{0} has already sampled {1} today, try again on "
                                        "a different day",
                                        "{0} is a planet name, and {1} is an item name, e.g. tin").format(
                                        planet.full_name, itemDisplayName(itemname)))
            return

        planet.samples_today.append(itemname)

        # Add new items to planet-- we might remove them in a sec, but this
        # also handles deleteing them from the player's items, so, meh
        planet.items.add_items(itemname, self.parent.state.items, rand_quantity)
        self.parent.updatePlayerItemsLabel()
        self.update()

        successful = random.randrange(0, 100) < const.ITEM_SAMPLE_SUCCESS_PERCENT
        if successful:
            # Sample succesful, update planet item browser to show new item we added
            self.parent.planetItemBrowser.update()

            # Reset item's value history
            item = planet.items.items[itemname]
            item.value_history = [item.value]

            title = self.tr("Good news!")
            msg = self.tr("Your sample achieved its intended purpose! "
                          "{0} is now actively trading in {1}.",
                          "{0} is a planet name, and {1} is an item name, e.g. tin").format(
                          planet.full_name, itemDisplayName(itemname))
        else:
            # Sample unsuccessful, delete items from planet
            planet.items.remove_items(itemname, rand_quantity)
            title = self.tr("Bad news!")
            msg = self.tr("Your sample was not well received, and {0} has decided not to "
                          "trade in {1}.",
                          "{0} is a planet name, and {1} is an item name, e.g. tin").format(
                          planet.full_name, itemDisplayName(itemname))


        infoDialog(self, title, message=msg)

    def dumpAllButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, self.tr("No items"), self.tr("You have no items to dump."))
            return

        proceed = yesNoDialog(self, self.tr("Dump everything?"),
                              message=self.tr("Are you sure you want to dump all your items? You "
                                              "will lose all the items in your ship, and you "
                                              "will not be able to get them back."))

        if not proceed:
            return

        self.parent.audio.play(self.parent.audio.DumpSound)
        self.parent.state.items.remove_all_items()
        self.parent.updatePlayerItemsLabel()
        self.update()

    def dumpButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, self.tr("No items"), self.tr("You have no items to dump."))
            return

        itemname = selectedItemName(self.table)
        if itemname is None:
            errorDialog(self, message=self.tr("Please select an item first!"))
            return

        dialog = DumpPlayerItem(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def sellButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, self.tr("No items"), self.tr("You have no items to sell."))
            return

        itemname = selectedItemName(self.table)
        if itemname is None:
            errorDialog(self, message=self.tr("Please select an item to sell first!"))
            return
        if itemname not in self.parent.state.current_planet.items.items:
            self.introduceNewItem(itemname)
            return

        dialog = Sell(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def sellAllButtonClicked(self):
        planet = self.parent.state.current_planet
        gain = 0

        if self.parent.state.items.count() == 0:
            errorDialog(self, self.tr("No items"), self.tr("You have no items to sell."))
            return

        items_for_sale_on_planet = False

        for name in self.parent.state.items.items:
            if name not in planet.items.items:
                continue

            items_for_sale_on_planet = True
            price = planet.items.items[name].value
            quantity = self.parent.state.items.items[name].quantity
            gain += price * quantity

        if not items_for_sale_on_planet:
            errorDialog(self, self.tr("Items cannot be sold"),
                        self.tr("This planet is not buying any of the items you are selling."))
            return

        proceed = yesNoDialog(self, self.tr("Sell all?"),
                              message=self.tr("Are you sure you want to sell all items "
                                              "that are currently being traded on {0}? (total "
                                              "gain: {1})", "{0} is a planet name").format(
                                              planet.full_name, formatNumber(gain)))

        if not proceed:
            return

        for name in list(self.parent.state.items.items.keys()):
            if name not in planet.items.items:
                continue

            quantity = self.parent.state.items.items[name].quantity
            planet.items.add_items(name, self.parent.state.items, quantity)
            self.parent.state.record_sale(name, quantity, planet.items.items[name].value)

        self.parent.audio.play(self.parent.audio.SellSound)
        self.parent.state.money += gain
        checkForMoneyBonus(self.parent)
        self.parent.infoBar.update()
        self.parent.planetItemBrowser.update()
        self.parent.updatePlayerItemsLabel()
        self.update()

    def warehouseButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, self.tr("No items"), self.tr("You have no items to put in the warehouse."))
            return

        if not atWarehouse(self):
            return

        if self.parent.state.warehouse_trips == self.parent.state.warehouse_trips_per_day:
            errorDialog(self, self.tr("Warehouse"), message=self.tr("You cannot put anything else "
                                                                    "in the warehouse until tomorrow"))
            return

        itemname = selectedItemName(self.table)
        if itemname is None:
            errorDialog(self, message=self.tr("Please select an item first!"))
            return

        dialog = PlayerToWarehouse(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def addRow(self, itemname):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)
        collection = self.parent.state.items

        item1 = itemNameCell(itemname)
        item2 = TableWidgetNumber(collection.items[itemname].quantity)

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)

    def populateTable(self):
        self.table.setRowCount(0)
        for name in self.parent.state.items.items:
            self.addRow(name)


def planet_item_browser_setup_header(browser):
    browser.table.setColumnCount(4)
    browser.table.setHorizontalHeaderLabels([translate("PlanetItemBrowser", 'Item type'),
                                             translate("PlanetItemBrowser", 'Quantity available'),
                                             translate("PlanetItemBrowser", 'Cost'),
                                             translate("PlanetItemBrowser", 'Base price delta')])
    header = browser.table.horizontalHeader()
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
    header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
    header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

def planet_item_browser_add_row(browser, planet, itemname):
    nextFreeRow = browser.table.rowCount()
    browser.table.insertRow(nextFreeRow)
    collection = planet.items

    base_value = collection.items[itemname].type.base_value
    value = collection.items[itemname].value
    delta = float(value - base_value) / (float(base_value) / 100.0)

    item1 = itemNameCell(itemname)
    item2 = TableWidgetNumber(collection.items[itemname].quantity)
    item3 = TableWidgetNumber(collection.items[itemname].value)
    item4 = TableWidgetNumber(delta, formatPercent(delta, 1))
    item2.setTextAlignment(QtCore.Qt.AlignHCenter)
    item3.setTextAlignment(QtCore.Qt.AlignHCenter)
    item4.setTextAlignment(QtCore.Qt.AlignHCenter)

    browser.table.setItem(nextFreeRow, 0, item1)
    browser.table.setItem(nextFreeRow, 1, item2)
    browser.table.setItem(nextFreeRow, 2, item3)
    browser.table.setItem(nextFreeRow, 3, item4)

def planet_item_browser_populate_table(browser, planet):
    browser.table.setRowCount(0)
    for name in planet.items.items:
        browser.addRow(name)


class TradingConsolePlanetDisplay(QtWidgets.QWidget):
    def __init__(self, parent, planet):
        super(TradingConsolePlanetDisplay, self).__init__(parent)

        self.planet = planet
        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.table = QtWidgets.QTableWidget()

        # Set alternating row colors, but keep default highlight color...
        default_palette = self.table.palette()
        default_highlight = default_palette.color(QtGui.QPalette.Highlight)
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Highlight, default_highlight)
        self.table.setPalette(palette)

        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(QtCore.Qt.NoFocus)
        self.table.setSortingEnabled(True)

        self.setupHeader()
        self.populateTable()
        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.table)

        self.table.resizeColumnsToContents()
        self.update()

    def setupHeader(self):
        planet_item_browser_setup_header(self)

    def update(self):
        self.table.setSortingEnabled(False)
        self.populateTable()
        self.table.setSortingEnabled(True)
        super(TradingConsolePlanetDisplay, self).update()

    def addRow(self, itemname):
        planet_item_browser_add_row(self, self.planet, itemname)

    def populateTable(self):
        planet_item_browser_populate_table(self, self.planet)


class PlanetItemBrowser(ItemBrowser):
    def __init__(self,  *args, **kwargs):
        super(PlanetItemBrowser, self).__init__(*args, **kwargs)

        self.add_button(self.tr("Buy item"), self.buyButtonClicked,
                        self.tr("buy one or more of the selected item from the current planet"))

    def setupHeader(self):
        planet_item_browser_setup_header(self)
        self.table.doubleClicked.connect(self.onDoubleClick)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            itemname = selectedItemName(self.table)
            if itemname is None:
                return

            item = self.parent.state.current_planet.items.items[itemname]

            dialog = PriceHistoryGraph(self.parent, item)
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.exec_()

    def onDoubleClick(self, signal):
        self.buyButtonClicked()

    def buyButtonClicked(self):
        itemname = selectedItemName(self.table)
        if itemname is None:
            errorDialog(self, self.tr("No item selected"),
                        message=self.tr("Please select an item to buy first!"))
            return

        if self.parent.state.current_planet.items.items[itemname].quantity == 0:
            errorDialog(self, self.tr("None available"),
                        message=self.tr("{0} has no {1} left to sell",
                                        "{0} is a planet name, and {1} is an item name, e.g. tin").format(
                                        self.parent.state.current_planet.full_name, itemDisplayName(itemname)))
            return

        if self.parent.state.capacity == self.parent.state.items.count():
            errorDialog(self, self.tr("Maximum capacity"),
                        message=self.tr("You have no more room on your ship. You need to increase your ship "
                                        "capacity, or sell some items, or dump some items, or move some items to "
                                        "the warehouse before you can buy more."))
            return

        dialog = Buy(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def addRow(self, itemname):
        planet_item_browser_add_row(self, self.parent.state.current_planet, itemname)

    def populateTable(self):
        planet_item_browser_populate_table(self, self.parent.state.current_planet)


class WarehouseItemBrowser(ItemBrowser):
    def __init__(self,  *args, **kwargs):
        super(WarehouseItemBrowser, self).__init__(*args, **kwargs)

        self.table.doubleClicked.connect(self.onDoubleClick)
        self.add_button(self.tr("Retrieve"), self.removeButtonClicked,
                        self.tr("move one or more of the selected item from the warehouse to your ship"))
        self.add_button(self.tr("Retrieve all"), self.removeAllButtonClicked,
                        self.tr("move all items from the warehouse to your ship"))
        self.add_button(self.tr("Dump"), self.dumpButtonClicked,
                        self.tr("dump one or more of the selected item from your warehouse"))
        self.add_button(self.tr("Dump all"), self.dumpAllButtonClicked, self.tr("dump all items from your warehouse"))

    def onDoubleClick(self):
        self.removeButtonClicked()

    def dumpAllButtonClicked(self):
        if self.parent.state.warehouse.count() == 0:
            errorDialog(self, self.tr("No items"), self.tr("You have no items to dump."))
            return

        proceed = yesNoDialog(self, self.tr("Dump everything?"),
                              message=self.tr("Are you sure you want to dump all your items? You "
                                              "will lose all the items in your warehouse, and you "
                                              "will not be able to get them back."))

        if not proceed:
            return

        self.parent.audio.play(self.parent.audio.DumpSound)
        self.parent.state.warehouse.remove_all_items()
        self.update()

    def dumpButtonClicked(self):
        totalitemcount = self.parent.state.warehouse.count()
        if totalitemcount == 0:
            errorDialog(self, self.tr("Warehouse"), message=self.tr("There is nothing in your warehouse to dump."))
            return

        itemname = selectedItemName(self.table)
        if itemname is None:
            errorDialog(self, message=self.tr("Please select an item first!"))
            return

        dialog = DumpWarehouseItem(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def removeAllButtonClicked(self):
        totalitemcount = self.parent.state.warehouse.count()
        if totalitemcount == 0:
            errorDialog(self, self.tr("Warehouse"), message=self.tr("There is nothing in your warehouse to retrieve."))
            return

        if not atWarehouse(self):
            return

        if self.parent.state.warehouse_trips == self.parent.state.warehouse_trips_per_day:
            errorDialog(self, self.tr("Warehouse"), message=self.tr("You cannot take anything else "
                                                                    "from the warehouse until tomorrow."))
            return

        capacity = self.parent.state.capacity - self.parent.state.items.count()
        itemcount = min(capacity, totalitemcount)

        if itemcount <= 0:
            errorDialog(self, self.tr("Maximum capacity"),
                        message=self.tr("You have no more room on your ship. You need to increase your ship "
                                        "capacity, or sell some items, or dump some items before you can "
                                        "retrieve items from the warehouse."))
            return

        if itemcount < totalitemcount:
            msg = translate("WarehouseItemBrowser",
                            "You do not have room for all items, the maximum number of items "
                            "that can be retrieved is %Ln. Are you sure you want to retrieve %Ln "
                            "items? ", None, itemcount)
        else:
            msg = self.tr("Are you sure you want to retrieve all items?")

        proceed = yesNoDialog(self.parent, self.tr("Are you sure?"), message=msg)
        if not proceed:
            return

        for name in list(self.parent.state.warehouse.items.keys()):
            if itemcount == 0:
                break

            item = self.parent.state.warehouse.items[name]
            quantity = min(itemcount, item.quantity)
            self.parent.state.items.add_items(name, self.parent.state.warehouse, quantity)
            itemcount -= quantity

        self.parent.audio.play(self.parent.audio.WhooshPopSound)
        self.parent.state.warehouse_trips += 1
        self.parent.warehouseItemBrowser.update()
        self.parent.playerItemBrowser.update()
        self.parent.updatePlayerItemsLabel()
        self.parent.infoBar.update()

    def removeButtonClicked(self):
        totalitemcount = self.parent.state.warehouse.count()
        if totalitemcount == 0:
            errorDialog(self, self.tr("Warehouse"), message=self.tr("There is nothing in your warehouse to remove."))
            return

        if not atWarehouse(self):
            return

        if self.parent.state.warehouse_trips == self.parent.state.warehouse_trips_per_day:
            errorDialog(self, self.tr("Warehouse"), message=self.tr("You cannot take anything else "
                                                                    "from the warehouse until tomorrow"))
            return

        itemname = selectedItemName(self.table)
        if itemname is None:
            errorDialog(self, message=self.tr("Please select an item first!"))
            return

        dialog = WarehouseToPlayer(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()


    def addRow(self, itemname):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)
        collection = self.parent.state.warehouse

        item1 = itemNameCell(itemname)
        item2 = TableWidgetNumber(collection.items[itemname].quantity)

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)

    def populateTable(self):
        self.table.setRowCount(0)
        for name in self.parent.state.warehouse.items:
            self.addRow(name)
