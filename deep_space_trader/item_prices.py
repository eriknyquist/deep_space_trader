from deep_space_trader.items import (
        common_item_types, medium_rare_item_types, rare_item_types
)

from PyQt5 import QtWidgets, QtCore, QtGui


types_lists = [
    common_item_types,
    medium_rare_item_types,
    rare_item_types
]

table_items = []
for l in types_lists:
    table_items += [(t.name, t.base_value) for t in l]


class PricesTable(QtWidgets.QDialog):
    def __init__(self, parent):
        super(PricesTable, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Item type', 'Base price'])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.table.setFocusPolicy(QtCore.Qt.NoFocus)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        self.table.resizeColumnsToContents()

        self.mainLayout.addWidget(self.table)
        self.setLayout(self.mainLayout)
        self.setWindowTitle("Prices")

        self.update()

    def addRow(self, name, value):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = QtWidgets.QTableWidgetItem(name)
        item2 = QtWidgets.QTableWidgetItem(str(value))

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)

    def populateTable(self):
        self.table.setRowCount(0)
        for table_item in table_items:
            self.addRow(*table_item)

    def update(self):
        self.populateTable()
        super(PricesTable, self).update()

    def sizeHint(self):
        return QtCore.QSize(600, 400)
