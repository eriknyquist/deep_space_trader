from deep_space_trader.store import Store
from deep_space_trader import constants as const
from deep_space_trader import config
from deep_space_trader.utils import errorDialog, yesNoDialog, infoDialog
from deep_space_trader.i18n import translate

from PyQt5 import QtWidgets, QtCore, QtGui


class ButtonBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super(ButtonBar, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QHBoxLayout(self)

        self.resetButton = QtWidgets.QPushButton(self.tr("Reset"))
        self.resetButton.clicked.connect(self.resetButtonClicked)
        self.mainLayout.addWidget(self.resetButton)

        self.storeButton = QtWidgets.QPushButton(self.tr("Go to store"))
        self.storeButton.clicked.connect(self.storeButtonClicked)
        self.mainLayout.addWidget(self.storeButton)

        self.dayButton = QtWidgets.QPushButton(self.tr("Go to next day"))
        self.dayButton.clicked.connect(self.dayButtonClicked)
        self.mainLayout.addWidget(self.dayButton)

        self.tooltipsEnabled = True
        self.setTooltips()

    def enableTooltips(self, enabled):
        self.tooltipsEnabled = enabled
        self.setTooltips()

    def setTooltips(self):
        if self.tooltipsEnabled:
            self.resetButton.setToolTip(self.tr("clears the current game progress and starts a new game"))
            self.storeButton.setToolTip(self.tr("opens the store window"))
            self.dayButton.setToolTip(self.tr("advances to the next day without travelling"))
        else:
            self.resetButton.setToolTip(None)
            self.storeButton.setToolTip(None)
            self.dayButton.setToolTip(None)

    def resetButtonClicked(self):
        proceed = yesNoDialog(self, self.tr("Are you sure?"),
                              message=self.tr("Are you sure you want to reset the game and "
                                              "lose your progress?"))
        if not proceed:
            return

        self.parent.reset()

    def storeButtonClicked(self):
        if self.parent.state.store_purchases >= self.parent.state.max_store_purchases_per_day:
            # (Counts passed to translate() must be plain variables, or pylupdate5 skips the string)
            max_purchases = self.parent.state.max_store_purchases_per_day
            errorDialog(self, self.tr("Sorry!"),
                        translate("ButtonBar", "You can only make %Ln store purchases per day. "
                                               "Come back tomorrow.", None, max_purchases))
            return

        dialog = Store(self.parent)
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        dialog.exec_()

    def dayButtonClicked(self):
        self.parent.advanceDay()
