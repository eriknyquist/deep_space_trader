import sys
import os
import random
import time
import qdarktheme

from deep_space_trader import config
from deep_space_trader.main_widget import MainWidget
from deep_space_trader.utils import gameStoryDialog, showAboutDialog, SOURCE_DIR, IMAGE_DIR, ICON_PATH

from PyQt5 import QtWidgets, QtGui, QtCore

from deep_space_trader import __version__ as package_version

def textDisplayWindow(title, message):
    msg = QtWidgets.QMessageBox()
    msg.setInformativeText(message)
    msg.setWindowTitle(title)
    self.setWindowIcon(QtGui.QIcon(ICON_PATH))
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, primary_screen):
        super(MainWindow, self).__init__()

        self.default_palette = QtWidgets.QApplication.instance().palette()
        self.primary_screen = primary_screen
        self.initUi()

    def initUi(self):
        self.iconPath = ICON_PATH
        self.setWindowIcon(QtGui.QIcon(self.iconPath))

        random.seed(time.time())
        self.widget = MainWidget(self.primary_screen, self)
        self.setCentralWidget(self.widget)

        self.quitAction = QtWidgets.QAction("Quit game", self)
        self.quitAction.setShortcut("Ctrl+q")
        self.quitAction.setStatusTip("Stop playing the game")
        self.quitAction.triggered.connect(self.widget.quit)

        self.scoresAction = QtWidgets.QAction("Show high scores", self)
        self.scoresAction.setShortcut("Ctrl+e")
        self.scoresAction.setStatusTip("Show table of high scores")
        self.scoresAction.triggered.connect(self.widget.showHighScores)

        self.aboutAction = QtWidgets.QAction("About", self)
        self.aboutAction.setShortcut("Ctrl+h")
        self.aboutAction.setStatusTip("About this game")
        self.aboutAction.triggered.connect(showAboutDialog)

        self.shareScoresAction = QtWidgets.QAction("High score sharing", self)
        self.shareScoresAction.setShortcut("Ctrl+r")
        self.shareScoresAction.setStatusTip("Share your high scores with others")
        self.shareScoresAction.triggered.connect(self.widget.shareHighScores)

        self.pricesAction = QtWidgets.QAction("Material prices", self)
        self.pricesAction.setShortcut("Ctrl+a")
        self.pricesAction.setStatusTip("Show base prices for tradeable items")
        self.pricesAction.triggered.connect(self.widget.showPrices)

        self.travelLogAction = QtWidgets.QAction("Show travel log", self)
        self.travelLogAction.setShortcut("Ctrl+s")
        self.travelLogAction.setStatusTip("Show a log of planets travelled to")
        self.travelLogAction.triggered.connect(self.widget.showTravelLog)

        self.darkThemeAction = QtWidgets.QAction("Dark theme", self)
        self.darkThemeAction.setShortcut("Ctrl+v")
        self.darkThemeAction.setStatusTip("Enable/disable dark theme")
        self.darkThemeAction.triggered.connect(self.toggleDarkTheme)
        self.darkThemeAction.setCheckable(True)
        self.darkThemeAction.setChecked(True)

        # Build menu bar
        menu = self.menuBar()
        fileMenu = menu.addMenu("File")
        fileMenu.addAction(self.scoresAction)
        fileMenu.addAction(self.shareScoresAction)
        fileMenu.addAction(self.quitAction)

        toolMenu = menu.addMenu("Tools")
        toolMenu.addAction(self.pricesAction)
        toolMenu.addAction(self.travelLogAction)

        viewMenu = menu.addMenu("View")
        viewMenu.addAction(self.darkThemeAction)

        helpMenu = menu.addMenu("Help")
        helpMenu.addAction(self.aboutAction)

    def enableDarkTheme(self, enabled):
        app = QtWidgets.QApplication.instance()

        if enabled:
            app.setPalette(qdarktheme.load_palette())
        else:
            app.setPalette(self.default_palette)

        app.setStyle('Fusion')
        app.setStyleSheet("")

    def toggleDarkTheme(self):
        self.enableDarkTheme(self.darkThemeAction.isChecked())

    def closeEvent(self, event):
        if self.widget.warningBeforeQuit():
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    app.setStyle('Fusion')
    font = QtWidgets.qApp.font()
    font.setPointSize(12)
    font.setFamily('monospace')
    app.setFont(font)

    win = MainWindow(app.primaryScreen())
    win.setWindowTitle("Deep Space Trader %s" % package_version)
    win.enableDarkTheme(True)
    win.show()

    if config.get_show_intro():
        dont_show_again = gameStoryDialog()
        config.set_show_intro(not dont_show_again)
        config.config_store()

    sys.exit(app.exec_())
