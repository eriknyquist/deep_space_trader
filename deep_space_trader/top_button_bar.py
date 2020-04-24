from deep_space_trader.store import Store
from deep_space_trader import constants as const
from deep_space_trader import config
from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog

from PyQt5 import QtWidgets, QtCore, QtGui


class ButtonBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super(ButtonBar, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QHBoxLayout(self)

        self.resetButton = QtWidgets.QPushButton("Reset")
        self.resetButton.clicked.connect(self.resetButtonClicked)
        self.mainLayout.addWidget(self.resetButton)

        self.storeButton = QtWidgets.QPushButton("Go to store")
        self.storeButton.clicked.connect(self.storeButtonClicked)
        self.mainLayout.addWidget(self.storeButton)

        self.dayButton = QtWidgets.QPushButton("Go to next day")
        self.dayButton.clicked.connect(self.dayButtonClicked)
        self.mainLayout.addWidget(self.dayButton)

    def resetButtonClicked(self):
        proceed = yesNoDialog(self, "Are you sure?",
                              message="Are you sure you want to reset the game and "
                                      "lose your progress?")
        if not proceed:
            return

        self.parent.reset()

    def storeButtonClicked(self):
        dialog = Store(self.parent)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def dayButtonClicked(self):
        self.parent.advanceDay()

    def useButtonClicked(self):
        dialog = StoreItemSelector(self.parent)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()
