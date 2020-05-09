import sys
import os
import random
import time

from deep_space_trader import config
from deep_space_trader.main_widget import MainWidget
from deep_space_trader.utils import gameStoryDialog, SOURCE_DIR, IMAGE_DIR

from PyQt5 import QtWidgets, QtGui, QtCore

from deep_space_trader import __maintainer__ as package_author
from deep_space_trader import __email__ as author_email
from deep_space_trader import __name__ as package_name
from deep_space_trader import __version__ as package_version


def textDisplayWindow(title, message):
    msg = QtWidgets.QMessageBox()
    msg.setInformativeText(message)
    msg.setWindowTitle(title)
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, primary_screen):
        super(MainWindow, self).__init__()

        self.primary_screen = primary_screen
        self.initUi()

    def initUi(self):
        self.iconPath = os.path.join(IMAGE_DIR, 'icon.png')
        self.setWindowIcon(QtGui.QIcon(self.iconPath))

        random.seed(time.time())
        self.widget = MainWidget(self.primary_screen, self)
        self.setCentralWidget(self.widget)

        self.quitAction = QtWidgets.QAction("Quit game", self)
        self.quitAction.setShortcut("Ctrl+q")
        self.quitAction.setStatusTip("Stop playing the game")
        self.quitAction.triggered.connect(self.widget.quit)

        self.scoresAction = QtWidgets.QAction("Show high scores", self)
        self.scoresAction.setShortcut("Ctrl+s")
        self.scoresAction.setStatusTip("Show table of high scores")
        self.scoresAction.triggered.connect(self.widget.showHighScores)

        self.pricesAction = QtWidgets.QAction("Material prices", self)
        self.pricesAction.setShortcut("Ctrl+p")
        self.pricesAction.setStatusTip("Show base prices for tradeable items")
        self.pricesAction.triggered.connect(self.widget.showPrices)

        self.shareScoresAction = QtWidgets.QAction("High score sharing", self)
        self.shareScoresAction.setShortcut("Ctrl+h")
        self.shareScoresAction.setStatusTip("Share your high scores with others")
        self.shareScoresAction.triggered.connect(self.widget.shareHighScores)

        # Build menu bar
        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        fileMenu.addAction(self.scoresAction)
        fileMenu.addAction(self.shareScoresAction)
        fileMenu.addAction(self.quitAction)

        helpMenu = menu.addMenu("Help")
        helpMenu.addAction(self.pricesAction)

    def closeEvent(self, event):
        if self.widget.warningBeforeQuit():
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow(app.primaryScreen())
    win.setWindowTitle("Deep Space Trader %s" % package_version)
    win.show()

    if config.get_show_intro():
        dont_show_again = gameStoryDialog()
        config.set_show_intro(not dont_show_again)
        config.config_store()

    sys.exit(app.exec_())

