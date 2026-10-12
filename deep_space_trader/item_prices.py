from deep_space_trader.items import (
        common_item_types, medium_rare_item_types, rare_item_types, contraband_item_types
)
from deep_space_trader.item_browsers import itemNameCell
from deep_space_trader.i18n import formatNumber
from deep_space_trader.utils import NUMBER_ALIGNMENT

from PyQt5 import QtWidgets, QtCore, QtGui


types_lists = [
    common_item_types,
    medium_rare_item_types,
    rare_item_types
]

table_items = []
for l in types_lists:
    table_items += [(t.name, t.base_value) for t in l]

contraband_table_items = [(t.name, t.base_value) for t in contraband_item_types]


class PricesTable(QtWidgets.QDialog):
    def __init__(self, parent):
        super(PricesTable, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget()

        # Set alternating row colors, but keep default highlight color...
        default_palette = self.table.palette()
        default_highlight = default_palette.color(QtGui.QPalette.Highlight)
        self.table.setAlternatingRowColors(True)
        palette = self.table.palette()
        palette.setColor(QtGui.QPalette.Highlight, default_highlight)
        self.table.setPalette(palette)

        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([self.tr('Item type'), self.tr('Base price')])
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
        self.setWindowTitle(self.tr("Prices"))

        self.update()

    def addRow(self, name, value):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = itemNameCell(name)
        item2 = QtWidgets.QTableWidgetItem(formatNumber(value))

        item2.setTextAlignment(NUMBER_ALIGNMENT)

        self.table.setItem(nextFreeRow, 0, item1)
        self.table.setItem(nextFreeRow, 1, item2)

    def addHeadingRow(self, text):
        """
        Row with a bold heading across the whole table
        """
        row = self.table.rowCount()
        self.table.insertRow(row)
        item = QtWidgets.QTableWidgetItem(text)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
        self.table.setItem(row, 0, item)
        self.table.setSpan(row, 0, 1, self.table.columnCount())

    def populateTable(self):
        self.table.clearSpans()
        self.table.setRowCount(0)
        for table_item in table_items:
            self.addRow(*table_item)

        self.addHeadingRow(self.tr("Contraband (only traded on black markets)"))
        for table_item in contraband_table_items:
            self.addRow(*table_item)

    def update(self):
        self.populateTable()
        super(PricesTable, self).update()

    def sizeHint(self):
        return QtCore.QSize(600, 400)
