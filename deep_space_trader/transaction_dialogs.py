from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog, checkForMoneyBonus, ICON_PATH

from PyQt5 import QtWidgets, QtCore, QtGui


class TransactionDialog(QtWidgets.QDialog):
    def __init__(self, parent, itemname, include_money=True):
        super(TransactionDialog, self).__init__(parent=parent)

        self.parent = parent
        self.itemName = itemname
        mainLayout = QtWidgets.QVBoxLayout(self)
        spinboxLayout = QtWidgets.QHBoxLayout()
        buttonLayout = QtWidgets.QHBoxLayout()

        self.description = QtWidgets.QLabel()
        moneyCount = QtWidgets.QLabel("(your money: {:,})".format(parent.state.money))

        self.spinboxLabel = QtWidgets.QLabel("")

        # Use a double spin box with 0 decimal places so we can get 64 bit integers
        self.spinbox = QtWidgets.QDoubleSpinBox()
        self.spinbox.setDecimals(0)

        self.spinbox.valueChanged.connect(self.valueChanged)
        self.spinbox.setMaximum(self.maximumQuantity())

        maxButton = QtWidgets.QPushButton("Max")
        maxButton.clicked.connect(self.maxButtonClicked)

        spinboxLayout.addWidget(self.spinboxLabel)
        spinboxLayout.addWidget(self.spinbox)
        spinboxLayout.addWidget(maxButton)

        self.acceptButton = QtWidgets.QPushButton()
        self.acceptButton.clicked.connect(self.acceptButtonClicked)
        buttonLayout.addWidget(self.acceptButton)

        cancelButton = QtWidgets.QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancelButtonClicked)
        buttonLayout.addWidget(cancelButton)

        mainLayout.addWidget(self.description)

        if include_money:
            mainLayout.addWidget(moneyCount)

        mainLayout.addLayout(spinboxLayout)
        mainLayout.addLayout(buttonLayout)

        self.setLayout(mainLayout)
        self.setWindowTitle("Buy items")
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

        self.description.setText("How much %s do you want to buy?" % self.itemName)
        self.acceptButton.setText("Buy")

    def acceptTransaction(self, quantity):
        self.parent.state.items.add_items(self.itemName,
                                          self.parent.state.current_planet.items,
                                          quantity, delete_empty=False)

        self.parent.state.money -= self.value * quantity

    def valueChanged(self):
        self.spinboxLabel.setText("Buy quantity (cost: {:,})".format(int(self.spinbox.value()) * self.value))

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
        self.description.setText("How much %s do you want to sell?" % self.itemName)
        self.acceptButton.setText("Sell")

    def acceptTransaction(self, quantity):
        self.parent.state.current_planet.items.add_items(self.itemName,
                                                         self.parent.state.items,
                                                         quantity)

        self.parent.state.money += self.value * quantity
        checkForMoneyBonus(self.parent)

    def valueChanged(self):
        self.spinboxLabel.setText("Sell quantity (gain: {:,})".format(int(self.spinbox.value()) * self.value))

    def maximumQuantity(self):
        return self.quantity


class PlayerToWarehouse(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.items.items[itemname].quantity

        super(PlayerToWarehouse, self).__init__(parent, itemname, include_money=False)
        self.description.setText("How much %s do you want to move to the warehouse?"
                                 % self.itemName)

        self.acceptButton.setText("Move")

    def acceptTransaction(self, quantity):
        self.parent.state.warehouse_puts += 1
        self.parent.state.warehouse.add_items(self.itemName,
                                              self.parent.state.items,
                                              quantity)

    def valueChanged(self):
        self.spinboxLabel.setText("Move quantity")

    def maximumQuantity(self):
        return self.quantity


class WarehouseToPlayer(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.warehouse.items[itemname].quantity

        super(WarehouseToPlayer, self).__init__(parent, itemname, include_money=False)
        self.description.setText("How much %s do you want to retrieve?"
                                 % self.itemName)

        self.acceptButton.setText("Move")

    def acceptTransaction(self, quantity):
        self.parent.state.warehouse_gets += 1
        self.parent.state.items.add_items(self.itemName,
                                          self.parent.state.warehouse,
                                          quantity)

    def valueChanged(self):
        self.spinboxLabel.setText("Move quantity")

    def maximumQuantity(self):
        return min(self.quantity, self.parent.state.capacity - self.parent.state.items.count())


class DumpWarehouseItem(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.warehouse.items[itemname].quantity

        super(DumpWarehouseItem, self).__init__(parent, itemname, include_money=False)
        self.description.setText("How much %s do you want to dump?" % self.itemName)
        self.acceptButton.setText("Dump")

    def acceptTransaction(self, quantity):
        proceed = yesNoDialog(self, "Dump items?",
                              message="Are you sure you want to dump {0:,} {1}? "
                              "You will lose these items from your warehouse, and you will "
                              "not be able to get them back.".format(quantity, self.itemName))
        if not proceed:
            return

        self.parent.state.warehouse.remove_items(self.itemName, quantity)
        infoDialog(self, "Success!", message="Items have been removed")

    def valueChanged(self):
        self.spinboxLabel.setText("Dump quantity")

    def maximumQuantity(self):
        return self.quantity


class DumpPlayerItem(TransactionDialog):
    def __init__(self, parent, itemname):
        self.quantity = parent.state.items.items[itemname].quantity

        super(DumpPlayerItem, self).__init__(parent, itemname, include_money=False)
        self.description.setText("How much %s do you want to dump?" % self.itemName)
        self.acceptButton.setText("Dump")

    def acceptTransaction(self, quantity):
        proceed = yesNoDialog(self, "Dump items?",
                              message="Are you sure you want to dump {0:,} {1}? "
                              "You will lose these items from your inventory, and you will "
                              "not be able to get them back.".format(quantity, self.itemName))
        if not proceed:
            return

        self.parent.state.items.remove_items(self.itemName, quantity)
        infoDialog(self, "Success!", message="Items have been removed")

    def valueChanged(self):
        self.spinboxLabel.setText("Dump quantity")

    def maximumQuantity(self):
        return self.quantity
