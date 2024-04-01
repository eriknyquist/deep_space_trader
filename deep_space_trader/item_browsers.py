import random

from deep_space_trader.transaction_dialogs import (
        Buy, Sell, PlayerToWarehouse, WarehouseToPlayer, DumpWarehouseItem,
        DumpPlayerItem
)

from deep_space_trader.price_graph import PriceHistoryGraph
from deep_space_trader import constants as const
from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog, checkForMoneyBonus

from PyQt5 import QtWidgets, QtCore, QtGui


class ItemBrowser(QtWidgets.QWidget):
    def __init__(self, parent):
        super(ItemBrowser, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.buttonLayout = QtWidgets.QHBoxLayout()

        self.table = QtWidgets.QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)

        self.setupHeader()
        self.populateTable()
        self.mainLayout.addLayout(self.buttonLayout)
        self.mainLayout.addWidget(self.table)

        self.table.resizeColumnsToContents()
        self.update()

    def setupHeader(self):
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Item type', 'Quantity'])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

    def update(self):
        self.populateTable()
        super(ItemBrowser, self).update()

    def add_button(self, text, on_click):
        b = QtWidgets.QPushButton(text)
        b.clicked.connect(on_click)
        self.buttonLayout.addWidget(b)

    def addRow(self, itemname):
        raise NotImplementedError()

    def populateTable(self):
        raise NotImplementedError()


class PlayerItemBrowser(ItemBrowser):
    def __init__(self,  *args, **kwargs):
        super(PlayerItemBrowser, self).__init__(*args, **kwargs)

        self.add_button("Sell items", self.sellButtonClicked)
        self.add_button("Sell all", self.sellAllButtonClicked)
        self.add_button("Add to warehouse", self.warehouseButtonClicked)
        self.add_button("Dump selected", self.dumpButtonClicked)
        self.add_button("Dump all", self.dumpAllButtonClicked)

        self.table.doubleClicked.connect(self.onDoubleClick)

    def onDoubleClick(self, signal):
        self.sellButtonClicked()

    def introduceNewItem(self, itemname):
        quantity = self.parent.state.items.items[itemname].quantity
        rand_quantity = random.randrange(*const.ITEM_SAMPLE_QUANTITY_RANGE)
        planet = self.parent.state.current_planet

        if quantity <= rand_quantity:
            rand_quantity = max(1, int(quantity / 2))

        msg = ("{0} has never been seen on {1}, and you will have to persuade them "
               "that it is worth buying. If you provide a free sample of {2} {0}, "
               "this may help your cause.<br><br>Provide a free sample of "
               "{2} {0}?".format(itemname, planet.full_name, rand_quantity))

        proceed = yesNoDialog(self, "Provide sample?", message=msg)
        if not proceed:
            return

        if itemname in planet.samples_today:
            errorDialog(self, "Already sampled today",
                        message="%s has already sampled %s today, try again on "
                                "a different day" % (planet.full_name, itemname))
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

            title = "Good news!"
            msg = ("Your sample achieved its intended purpose! "
                    "%s is now actively trading in %s." % (planet.full_name, itemname))
        else:
            # Sample unsuccessful, delete items from planet
            planet.items.remove_items(itemname, rand_quantity)
            title = "Bad news!"
            msg = ("Your sample was not well received, and %s has decided not to "
                   "trade in %s." % (planet.full_name, itemname))


        infoDialog(self, title, message=msg)

    def dumpAllButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, "No items", "You have no items to dump.")
            return

        proceed = yesNoDialog(self, "Dump everything?",
                              message="Are you sure you want to dump all your items? You "
                                      "will lose all the items in your inventory, and you "
                                      "will not be able to get them back.")

        if not proceed:
            return

        self.parent.state.items.remove_all_items()
        self.parent.updatePlayerItemsLabel()
        self.update()

    def dumpButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, "No items", "You have no items to dump.")
            return

        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select an item first!")
            return

        itemname = self.table.item(selectedRow, 0).text()
        dialog = DumpPlayerItem(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def sellButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, "No items", "You have no items to sell.")
            return

        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select an item to sell first!")
            return
        itemname = self.table.item(selectedRow, 0).text()
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
            errorDialog(self, "No items", "You have no items to sell.")
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
            errorDialog(self,  "Items cannot be sold",
                        "This planet is not buying any of the items you are selling.")
            return

        proceed = yesNoDialog(self, "Sell all?",
                              message="Are you sure you want to sell all items "
                              "that are currently being traded on {0}? (total "
                              "gain: {1:,})".format(planet.full_name, gain))

        if not proceed:
            return

        for name in list(self.parent.state.items.items.keys()):
            if name not in planet.items.items:
                continue

            quantity = self.parent.state.items.items[name].quantity
            planet.items.add_items(name, self.parent.state.items, quantity)
            self.parent.state.record_sale(name, quantity, planet.items.items[name].value)

        self.parent.state.money += gain
        checkForMoneyBonus(self.parent)
        self.parent.infoBar.update()
        self.parent.planetItemBrowser.update()
        self.parent.updatePlayerItemsLabel()
        self.update()

    def warehouseButtonClicked(self):
        if self.parent.state.items.count() == 0:
            errorDialog(self, "No items", "You have no items to put in the warehouse.")
            return

        if self.parent.state.warehouse_puts == self.parent.state.warehouse_puts_per_day:
            errorDialog(self, "Warehouse", message="You cannot put anything else "
                                                   "in the warehouse until tomorrow")
            return

        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select an item first!")
            return

        itemname = self.table.item(selectedRow, 0).text()
        dialog = PlayerToWarehouse(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def addRow(self, itemname):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)
        collection = self.parent.state.items

        item1 = QtWidgets.QTableWidgetItem(itemname)
        item2 = QtWidgets.QTableWidgetItem('{:,}'.format(collection.items[itemname].quantity))

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)

    def populateTable(self):
        self.table.setRowCount(0)
        for name in self.parent.state.items.items:
            self.addRow(name)


class PlanetItemBrowser(ItemBrowser):
    def __init__(self,  *args, **kwargs):
        super(PlanetItemBrowser, self).__init__(*args, **kwargs)

        self.add_button("Buy item", self.buyButtonClicked)

    def setupHeader(self):
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['Item type', 'Quantity available', 'Cost'])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        self.table.doubleClicked.connect(self.onDoubleClick)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Return:
            itemname = self.table.item(self.table.currentRow(), 0).text()
            item = self.parent.state.current_planet.items.items[itemname]

            dialog = PriceHistoryGraph(self.parent, item)
            dialog.setWindowModality(QtCore.Qt.ApplicationModal)
            dialog.exec_()

    def onDoubleClick(self, signal):
        self.buyButtonClicked()

    def buyButtonClicked(self):
        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, "No item selected",
                        message="Please select an item to buy first!")
            return

        itemname = self.table.item(selectedRow, 0).text()
        if self.parent.state.current_planet.items.items[itemname].quantity == 0:
            errorDialog(self, "None available",
                        message="%s has no %s left to sell" %
                        (self.parent.state.current_planet.full_name, itemname))
            return

        dialog = Buy(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def addRow(self, itemname):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)
        collection = self.parent.state.current_planet.items

        item1 = QtWidgets.QTableWidgetItem(itemname)
        item2 = QtWidgets.QTableWidgetItem('{:,}'.format(collection.items[itemname].quantity))
        item3 = QtWidgets.QTableWidgetItem(str(collection.items[itemname].value))

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)
        item3.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)
        self.table.setItem(nextFreeRow, 2, item3)

    def populateTable(self):
        self.table.setRowCount(0)
        for name in self.parent.state.current_planet.items.items:
            self.addRow(name)


class WarehouseItemBrowser(ItemBrowser):
    def __init__(self,  *args, **kwargs):
        super(WarehouseItemBrowser, self).__init__(*args, **kwargs)

        self.table.doubleClicked.connect(self.onDoubleClick)
        self.add_button("Retrieve items", self.removeButtonClicked)
        self.add_button("Retrieve all", self.removeAllButtonClicked)
        self.add_button("Dump selected", self.dumpButtonClicked)
        self.add_button("Dump all", self.dumpAllButtonClicked)

    def onDoubleClick(self):
        self.removeButtonClicked()

    def dumpAllButtonClicked(self):
        if self.parent.state.warehouse.count() == 0:
            errorDialog(self, "No items", "You have no items to dump.")
            return

        proceed = yesNoDialog(self, "Dump everything?",
                              message="Are you sure you want to dump all your items? You "
                                      "will lose all the items in your warehouse, and you "
                                      "will not be able to get them back.")

        if not proceed:
            return

        self.parent.state.warehouse.remove_all_items()
        self.update()

    def dumpButtonClicked(self):
        totalitemcount = self.parent.state.warehouse.count()
        if totalitemcount == 0:
            errorDialog(self, "Warehouse", message="There is nothing in your warehouse to dump.")
            return

        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select an item first!")
            return

        itemname = self.table.item(selectedRow, 0).text()
        dialog = DumpWarehouseItem(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def removeAllButtonClicked(self):
        totalitemcount = self.parent.state.warehouse.count()
        if totalitemcount == 0:
            errorDialog(self, "Warehouse", message="There is nothing in your warehouse to retrieve.")
            return

        if self.parent.state.warehouse_gets == self.parent.state.warehouse_gets_per_day:
            errorDialog(self, "Warehouse", message="You cannot take anything else "
                                                   "from the warehouse until tomorrow.")
            return

        capacity = self.parent.state.capacity - self.parent.state.items.count()
        itemcount = min(capacity, totalitemcount)

        if itemcount < totalitemcount:
            msg = (
                "You do not have room for all items, the maximum number of items "
                "that can be retrieved is {0:,}. Are you sure you want to retrieve {0:,} "
                "items? ".format(itemcount)
            )
        else:
            msg = "Are you sure you want to retrieve all items?"

        proceed = yesNoDialog(self.parent, "Are you sure?", message=msg)
        if not proceed:
            return

        for name in list(self.parent.state.warehouse.items.keys()):
            if itemcount == 0:
                break

            item = self.parent.state.warehouse.items[name]
            quantity = min(itemcount, item.quantity)
            self.parent.state.items.add_items(name, self.parent.state.warehouse, quantity)
            itemcount -= quantity

        self.parent.state.warehouse_gets += 1
        self.parent.warehouseItemBrowser.update()
        self.parent.playerItemBrowser.update()
        self.parent.updatePlayerItemsLabel()

    def removeButtonClicked(self):
        totalitemcount = self.parent.state.warehouse.count()
        if totalitemcount == 0:
            errorDialog(self, "Warehouse", message="There is nothing in your warehouse to retrieve.")
            return

        if self.parent.state.warehouse_gets == self.parent.state.warehouse_gets_per_day:
            errorDialog(self, "Warehouse", message="You cannot take anything else "
                                                   "from the warehouse until tomorrow")
            return

        selectedRow = self.table.currentRow()
        if selectedRow < 0:
            errorDialog(self, message="Please select an item first!")
            return

        itemname = self.table.item(selectedRow, 0).text()
        dialog = WarehouseToPlayer(self.parent, itemname)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()


    def addRow(self, itemname):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)
        collection = self.parent.state.warehouse

        item1 = QtWidgets.QTableWidgetItem(itemname)
        item2 = QtWidgets.QTableWidgetItem('{:,}'.format(collection.items[itemname].quantity))

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)

    def populateTable(self):
        self.table.setRowCount(0)
        for name in self.parent.state.warehouse.items:
            self.addRow(name)
