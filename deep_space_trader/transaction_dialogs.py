from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog, checkForMoneyBonus, ICON_PATH
from deep_space_trader.items import itemDisplayName
from deep_space_trader.i18n import translate, formatNumber

from PyQt5 import QtWidgets, QtCore, QtGui


class TransactionDialog(QtWidgets.QDialog):
    # Text in this base class uses translate("TransactionDialog", ...) rather than
    # self.tr(), since self.tr() would look it up under the subclass name
    def __init__(self, parent, itemname, include_money=True):
        super(TransactionDialog, self).__init__(parent=parent)

        self.parent = parent
        self.itemName = itemname
        mainLayout = QtWidgets.QVBoxLayout(self)
        spinboxLayout = QtWidgets.QHBoxLayout()
        buttonLayout = QtWidgets.QHBoxLayout()

        self.description = QtWidgets.QLabel()
        moneyCount = QtWidgets.QLabel(translate("TransactionDialog", "(your money: {0})").format(
                                      formatNumber(parent.state.money)))

        self.spinboxLabel = QtWidgets.QLabel("")

        # Use a double spin box with 0 decimal places so we can get 64 bit integers
        self.spinbox = QtWidgets.QDoubleSpinBox()
        self.spinbox.setDecimals(0)

        self.spinbox.valueChanged.connect(self.valueChanged)
        self.spinbox.setMaximum(self.maximumQuantity())

        maxButton = QtWidgets.QPushButton(translate("TransactionDialog", "Max"))
        maxButton.clicked.connect(self.maxButtonClicked)

        spinboxLayout.addWidget(self.spinboxLabel)
        spinboxLayout.addWidget(self.spinbox)
        spinboxLayout.addWidget(maxButton)

        self.acceptButton = QtWidgets.QPushButton()
        self.acceptButton.clicked.connect(self.acceptButtonClicked)
        buttonLayout.addWidget(self.acceptButton)

        cancelButton = QtWidgets.QPushButton(translate("TransactionDialog", "Cancel"))
        cancelButton.clicked.connect(self.cancelButtonClicked)
        buttonLayout.addWidget(cancelButton)

        mainLayout.addWidget(self.description)

        if include_money:
            mainLayout.addWidget(moneyCount)

        mainLayout.addLayout(spinboxLayout)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

        self.valueChanged()

    def maxButtonClicked(self):
        self.spinbox.setValue(self.maximumQuantity())

    def acceptButtonClicked(self):
        value = int(self.spinbox.value())
        if value == 0:
            return

        self.acceptTransaction(value)
        self.parent.playerItemBrowser.update()
        self.parent.planetItemBrowser.update()
        self.parent.warehouseItemBrowser.update()
        self.parent.infoBar.update()
        self.parent.updatePlayerItemsLabel()
        self.accept()

    def cancelButtonClicked(self):
        self.reject()

    def acceptTransaction(self, quantity):
        raise NotImplementedError()

    def valueChanged(self):
        raise NotImplementedError()

    def maximumQuantity(self):
        raise NotImplementedError()


class Buy(TransactionDialog):
    def __init__(self, parent, itemname):
        self.value = parent.state.current_planet.items.items[itemname].value
        self.quantity = parent.state.current_planet.items.items[itemname].quantity

        super(Buy, self).__init__(parent, itemname, include_money=True)

        self.description.setText(self.tr("How much {0} do you want to buy?",
                                         "{0} is an item name, e.g. tin").format(itemDisplayName(self.itemName)))
        self.acceptButton.setText(self.tr("Buy"))
        self.setWindowTitle(self.tr("Buy items"))

    def acceptTransaction(self, quantity):
        self.parent.state.items.add_items(self.itemName,
                                          self.parent.state.current_planet.items,
                                          quantity, delete_empty=False)

        self.parent.audio.play(self.parent.audio.WhooshPopSound)
        self.parent.state.money -= self.value * quantity
        self.parent.state.record_purchase(self.itemName, quantity, self.value)

    def valueChanged(self):
        self.spinboxLabel.setText(self.tr("Buy quantity (cost: {0})").format(
                                  formatNumber(int(self.spinbox.value()) * self.value)))

    def maximumQuantity(self):
        capacity = self.parent.state.capacity - self.parent.state.items.count()
        max_buy = int(self.parent.state.money / self.value)
        return min(max_buy, capacity, self.quantity)

    def sourceCollection(self):
        return self.parent.state.current_planet.items


class Sell(TransactionDialog):
    def __init__(self, parent, itemname):
        self.value = parent.state.current_planet.items.items[itemname].value
        self.quantity = parent.state.items.items[itemname].quantity

        super(Sell, self).__init__(parent, itemname, include_money=False)
        self.description.setText(self.tr("How much {0} do you want to sell?",
                                         "{0} is an item name, e.g. tin").format(itemDisplayName(self.itemName)))
        self.acceptButton.setText(self.tr("Sell"))
        self.setWindowTitle(self.tr("Sell items"))

    def acceptTransaction(self, quantity):
        self.parent.state.current_planet.items.add_items(self.itemName,
                                                         self.parent.state.items,
                                                         quantity)

        self.parent.state.money += self.value * quantity
        self.parent.state.record_sale(self.itemName, quantity, self.value)
        self.parent.audio.play(self.parent.audio.SellSound)
        checkForMoneyBonus(self.parent)

    def valueChanged(self):
        self.spinboxLabel.setText(self.tr("Sell quantity (gain: {0})").format(
                                  formatNumber(int(self.spinbox.value()) * self.value)))

    def maximumQuantity(self):
        return self.quantity


class PlayerToWarehouse(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.items.items[itemname].quantity

        super(PlayerToWarehouse, self).__init__(parent, itemname, include_money=False)
        self.description.setText(self.tr("How much {0} do you want to move to the warehouse?",
                                         "{0} is an item name, e.g. tin").format(itemDisplayName(self.itemName)))

        self.acceptButton.setText(self.tr("Move"))
        self.setWindowTitle(self.tr("Move to warehouse"))

    def acceptTransaction(self, quantity):
        self.parent.audio.play(self.parent.audio.WhooshPopSound)
        self.parent.state.warehouse_trips += 1
        self.parent.state.warehouse.add_items(self.itemName,
                                              self.parent.state.items,
                                              quantity)

    def valueChanged(self):
        self.spinboxLabel.setText(self.tr("Move quantity"))

    def maximumQuantity(self):
        return self.quantity


class WarehouseToPlayer(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.warehouse.items[itemname].quantity

        super(WarehouseToPlayer, self).__init__(parent, itemname, include_money=False)
        self.description.setText(self.tr("How much {0} do you want to retrieve?",
                                         "{0} is an item name, e.g. tin").format(itemDisplayName(self.itemName)))

        self.acceptButton.setText(self.tr("Move"))
        self.setWindowTitle(self.tr("Retrieve from warehouse"))

    def acceptTransaction(self, quantity):
        self.parent.audio.play(self.parent.audio.WhooshPopSound)
        self.parent.state.warehouse_trips += 1
        self.parent.state.items.add_items(self.itemName,
                                          self.parent.state.warehouse,
                                          quantity)

    def valueChanged(self):
        self.spinboxLabel.setText(self.tr("Move quantity"))

    def maximumQuantity(self):
        return min(self.quantity, self.parent.state.capacity - self.parent.state.items.count())


class DumpWarehouseItem(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.warehouse.items[itemname].quantity

        super(DumpWarehouseItem, self).__init__(parent, itemname, include_money=False)
        self.description.setText(self.tr("How much {0} do you want to dump?",
                                         "{0} is an item name, e.g. tin").format(itemDisplayName(self.itemName)))
        self.acceptButton.setText(self.tr("Dump"))
        self.setWindowTitle(self.tr("Dump warehouse items"))

    def acceptTransaction(self, quantity):
        proceed = yesNoDialog(self, self.tr("Dump items?"),
                              message=translate("DumpWarehouseItem",
                                                "Are you sure you want to dump %Ln {0}? "
                                                "You will lose these items from your warehouse, and you will "
                                                "not be able to get them back.",
                                                "{0} is an item name, e.g. tin",
                                                quantity).format(itemDisplayName(self.itemName)))
        if not proceed:
            return

        self.parent.audio.play(self.parent.audio.DumpSound)
        self.parent.state.warehouse.remove_items(self.itemName, quantity)

    def valueChanged(self):
        self.spinboxLabel.setText(self.tr("Dump quantity"))

    def maximumQuantity(self):
        return self.quantity


class DumpPlayerItem(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.items.items[itemname].quantity

        super(DumpPlayerItem, self).__init__(parent, itemname, include_money=False)
        self.description.setText(self.tr("How much {0} do you want to dump?",
                                         "{0} is an item name, e.g. tin").format(itemDisplayName(self.itemName)))
        self.acceptButton.setText(self.tr("Dump"))
        self.setWindowTitle(self.tr("Dump player items"))

    def acceptTransaction(self, quantity):
        proceed = yesNoDialog(self, self.tr("Dump items?"),
                              message=translate("DumpPlayerItem",
                                                "Are you sure you want to dump %Ln {0}? "
                                                "These items will be removed from your ship, and you will "
                                                "not be able to get them back.",
                                                "{0} is an item name, e.g. tin",
                                                quantity).format(itemDisplayName(self.itemName)))
        if not proceed:
            return

        self.parent.audio.play(self.parent.audio.DumpSound)
        self.parent.state.items.remove_items(self.itemName, quantity)

    def valueChanged(self):
        self.spinboxLabel.setText(self.tr("Dump quantity"))

    def maximumQuantity(self):
        return self.quantity
