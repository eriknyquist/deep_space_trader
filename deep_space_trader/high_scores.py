import json

from deep_space_trader import config
from deep_space_trader.utils import yesNoDialog, errorDialog, infoDialog
from deep_space_trader.utils import scores_encode, scores_decode

from PyQt5 import QtWidgets, QtCore, QtGui


class HighScoreTable(QtWidgets.QDialog):
    def __init__(self, parent):
        super(HighScoreTable, self).__init__(parent)

        self.parent = parent
        self.mainLayout = QtWidgets.QVBoxLayout(self)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['Name', 'Score'])
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
        self.setWindowTitle("High scores")

        self.update()

    def addRow(self, name, score):
        nextFreeRow = self.table.rowCount()
        self.table.insertRow(nextFreeRow)

        item1 = QtWidgets.QTableWidgetItem(name)
        item2 = QtWidgets.QTableWidgetItem('{:,}'.format(score))

        item2.setTextAlignment(QtCore.Qt.AlignHCenter)

        self.table.setItem(nextFreeRow, 0, item1)
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
        displayGroup = QtWidgets.QGroupBox("Copy this string to share your "
                                           "scores with someone else")
        displayGroup.setLayout(displayLayout)
        self.mainLayout.addWidget(displayGroup)

        inputLayout = QtWidgets.QVBoxLayout()
        self.inputScores = QtWidgets.QTextEdit()
        inputLayout.addWidget(self.inputScores)

        self.inputButton = QtWidgets.QPushButton("Add high scores")
        self.inputButton.clicked.connect(self.inputButtonClicked)
        inputLayout.addWidget(self.inputButton)

        inputGroup = QtWidgets.QGroupBox("Paste someone else's string here to "
                                         "add their scores to your high score "
                                         "table")

        inputGroup.setLayout(inputLayout)
        self.mainLayout.addWidget(inputGroup)

        self.setLayout(self.mainLayout)
        self.setWindowTitle("High score sharing")

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
            errorDialog(self, "Error", message="Failed to decode high scores")
            return

        scores_msg = "The string you added contains the following scores:<br><br>"
        scores_msg += "<br>".join(['{0} ({1:,})'.format(x[0], x[1]) for x in scores])
        scores_msg += "<br><br>"
        scores_msg += "Are you sure you want to add them to your high scores?"

        proceed = yesNoDialog(self, "Add scores?", message=scores_msg)
        if not proceed:
            return

        for name, score in scores:
            config.add_highscore(name, score)

        infoDialog(self, "Success", "Scores added successfully")

    def update(self):
        super(HighScoreSharing, self).update()

        data = json.dumps(config.get_highscores())
        b64 = scores_encode(bytes(data, encoding='utf8'))
        self.displayScores.setText(b64.decode('utf-8'))
