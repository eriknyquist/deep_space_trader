from deep_space_trader.store import Store
from deep_space_trader.utils import errorDialog, yesNoDialog
from deep_space_trader.i18n import translate
from deep_space_trader import icons

from PyQt5 import QtWidgets, QtCore


class ButtonBar(QtWidgets.QWidget):
    def __init__(self, parent):
        super(ButtonBar, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QHBoxLayout(self)

        self.storeButton = QtWidgets.QPushButton(self.tr("Go to store"))
        self.storeButton.clicked.connect(self.storeButtonClicked)
        icons.setButtonIcon(self.storeButton, icons.STORE)
        self.mainLayout.addWidget(self.storeButton, 2)

        self.dayButton = QtWidgets.QPushButton(self.tr("Go to next day"))
        self.dayButton.clicked.connect(self.dayButtonClicked)
        icons.setButtonIcon(self.dayButton, icons.NEXT_DAY)
        self.mainLayout.addWidget(self.dayButton, 2)

        # Reset is last and narrower, so it doesn't look like the main button,
        # and isn't the one that gets the keyboard focus when the game starts
        self.resetButton = QtWidgets.QPushButton(self.tr("Reset"))
        self.resetButton.clicked.connect(self.resetButtonClicked)
        icons.setButtonIcon(self.resetButton, icons.RESET)
        self.mainLayout.addWidget(self.resetButton, 1)

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

        # Reputation recovers a little each day. (Travelling refreshes it along
        # with the distances, so this is only needed here)
        self.parent.locationBrowser.refreshReputations()
