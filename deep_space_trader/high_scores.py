import json

from deep_space_trader import config
from deep_space_trader.utils import yesNoDialog, errorDialog, infoDialog
from deep_space_trader.utils import scores_encode, scores_decode
from deep_space_trader.i18n import formatNumber

from PyQt5 import QtWidgets, QtCore, QtGui


class HighScoreTable(QtWidgets.QDialog):
    def __init__(self, parent):
        super(HighScoreTable, self).__init__(parent)

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
        self.table.setHorizontalHeaderLabels([self.tr('Name'), self.tr('Score')])
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
        self.setWindowTitle(self.tr("High scores"))
        self.update()
        self.adjustSize()

    def addRow(self, name, score):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        if nextFreeRow == 0:
            name = self.tr("{0} <i><b>(1st place)</b></i>", "{0} is the player's name").format(name)
        elif nextFreeRow == 1:
            name = self.tr("{0} <i><b>(2nd place)</b></i>", "{0} is the player's name").format(name)
        elif nextFreeRow == 2:
            name = self.tr("{0} <i><b>(3rd place)</b></i>", "{0} is the player's name").format(name)

        widgetText = QtWidgets.QLabel(name)
        item1 = QtWidgets.QTableWidgetItem(name)
        item2 = QtWidgets.QTableWidgetItem(formatNumber(score))

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        #self.table.setItem(nextFreeRow, 0, item1)
        self.table.setCellWidget(nextFreeRow, 0, widgetText)
        self.table.setItem(nextFreeRow, 1, item2)

    def populateTable(self):
        self.table.setRowCount(0)
        for score_info in config.get_highscores():
            self.addRow(*score_info)

    def update(self):
        self.populateTable()
        super(HighScoreTable, self).update()

    def sizeHint(self):
        return QtCore.QSize(600, 400)


class HighScoreSharing(QtWidgets.QDialog):
    def __init__(self, parent):
        super(HighScoreSharing, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        displayLayout = QtWidgets.QHBoxLayout()
        self.displayScores = QtWidgets.QTextEdit()
        self.displayScores.setReadOnly(True)
        displayLayout.addWidget(self.displayScores)
        displayGroup = QtWidgets.QGroupBox(self.tr("Copy this string to share your "
                                                   "scores with someone else"))
        displayGroup.setLayout(displayLayout)
        self.mainLayout.addWidget(displayGroup)

        inputLayout = QtWidgets.QVBoxLayout()
        self.inputScores = QtWidgets.QTextEdit()
        inputLayout.addWidget(self.inputScores)

        self.inputButton = QtWidgets.QPushButton(self.tr("Add high scores"))
        self.inputButton.clicked.connect(self.inputButtonClicked)
        inputLayout.addWidget(self.inputButton)

        inputGroup = QtWidgets.QGroupBox(self.tr("Paste someone else's string here to "
                                                 "add their scores to your high score "
                                                 "table"))

        inputGroup.setLayout(inputLayout)
        self.mainLayout.addWidget(inputGroup)

        self.setLayout(self.mainLayout)
        self.setWindowTitle(self.tr("High score sharing"))

        self.update()

    def inputButtonClicked(self):
        text = self.inputScores.toPlainText().strip()
        if text == "":
            return

        try:
            b64 = bytes(text, encoding='utf8')
            decoded = scores_decode(b64).decode('utf-8')
            scores = json.loads(decoded)
        except:
            errorDialog(self, self.tr("Error"), message=self.tr("Failed to decode high scores"))
            return

        scores_msg = self.tr("The string you added contains the following scores:")
        scores_msg += "<br><br>"
        scores_msg += "<br>".join(['{0} ({1})'.format(x[0], formatNumber(x[1])) for x in scores])
        scores_msg += "<br><br>"
        scores_msg += self.tr("Are you sure you want to add them to your high scores?")

        proceed = yesNoDialog(self, self.tr("Add scores?"), message=scores_msg)
        if not proceed:
            return

        for name, score in scores:
            config.add_highscore(name, score)

        infoDialog(self, self.tr("Success"), self.tr("Scores added successfully"))
        config.config_store()

    def update(self):
        super(HighScoreSharing, self).update()

        data = json.dumps(config.get_highscores())
        b64 = scores_encode(bytes(data, encoding='utf8'))
        self.displayScores.setText(b64.decode('utf-8'))
