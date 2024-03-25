import hashlib
import base64
import os
import sys

from PyQt5 import QtWidgets, QtCore, QtGui

from deep_space_trader import constants as const

DATA_ITER = 99
PWD_ITER = 72
PWD = b'g\x54n70erew feasf90s gf\xff\x0f\x290780 9\x02ng7804\x00>:": k'

if getattr(sys, 'frozen', False):
    SOURCE_DIR = os.path.dirname(sys.executable)
else:
    SOURCE_DIR = os.path.dirname(__file__)

IMAGE_DIR = os.path.join(SOURCE_DIR, 'images')
ICON_PATH = os.path.join(IMAGE_DIR, 'icon.png')


class ScrollableTextDisplay(QtWidgets.QDialog):
    def __init__(self, title, text):
        super(ScrollableTextDisplay, self).__init__()

        mainLayout = QtWidgets.QVBoxLayout(self)

        self.text_browser = QtWidgets.QTextBrowser()
        self.text_browser.append(text)

        mainLayout.addWidget(self.text_browser)

        self.setLayout(mainLayout)
        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        self.setMinimumSize(480, 200)

class InfoDialog(QtWidgets.QDialog):
    def __init__(self, title, text, cancelable=True):
        super(InfoDialog, self).__init__()

        self.dont_show_again = False
        mainLayout = QtWidgets.QVBoxLayout(self)
        textLayout = QtWidgets.QHBoxLayout()
        textGroup = QtWidgets.QGroupBox()
        self.text = QtWidgets.QLabel(text)

        self.text.setText(text)
        self.text.setWordWrap(True)
        textLayout.addWidget(self.text)
        textGroup.setLayout(textLayout)
        mainLayout.addWidget(textGroup)

        if cancelable:
            checkboxLabel = QtWidgets.QLabel("Don't show this message again")
            self.checkbox = QtWidgets.QCheckBox()
            self.checkbox.stateChanged.connect(self.checkboxClicked)
            self.checkboxLayout = QtWidgets.QHBoxLayout()
            self.checkboxLayout.addWidget(checkboxLabel)
            self.checkboxLayout.addWidget(self.checkbox)
            mainLayout.addLayout(self.checkboxLayout)

        self.setLayout(mainLayout)
        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))

    def checkboxClicked(self):
        self.dont_show_again = self.checkbox.isChecked()

def showAboutDialog():
    dialog = InfoDialog("Deep Space Trader", const.GAME_ABOUT_TEXT, cancelable=False)
    dialog.setWindowModality(QtCore.Qt.ApplicationModal)
    dialog.exec_()

def gameStoryDialog():
    dialog = InfoDialog("Deep Space Trader", const.GAME_INTRO_TEXT)
    dialog.setWindowModality(QtCore.Qt.ApplicationModal)
    dialog.exec_()
    return dialog.dont_show_again

def yesNoDialog(parent, header="", message="Are you sure?"):
    reply = QtWidgets.QMessageBox.question(parent, header, message,
                                           (QtWidgets.QMessageBox.Yes |
                                           QtWidgets.QMessageBox.No |
                                           QtWidgets.QMessageBox.Cancel),
                                           QtWidgets.QMessageBox.Cancel)

    return reply == QtWidgets.QMessageBox.Yes

def errorDialog(parent, heading="Error", message="Unrecoverable error occurred"):
    msg = QtWidgets.QMessageBox(parent)
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(heading)
    msg.setInformativeText(message)
    msg.setWindowTitle("Error")
    msg.setWindowIcon(QtGui.QIcon(ICON_PATH))
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()

def infoDialog(parent, heading="", message=""):
    msg = QtWidgets.QMessageBox(parent)
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText(heading + "<br><br>" + message)
    msg.setWindowTitle("Information")
    msg.setWindowIcon(QtGui.QIcon(ICON_PATH))
    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
    msg.exec_()


def checkForMoneyBonus(parent):
    new_days = None
    new_store_purchases = None

    if ((parent.state.money >= const.BONUS_1_MONEY) and
        (parent.state.max_days < const.BONUS_1_MAX_DAYS)):
        # Player gets bonus #1
        new_days = const.BONUS_1_MAX_DAYS
        new_store_purchases = parent.state.max_store_purchases_per_day + 1

    if ((parent.state.money >= const.BONUS_2_MONEY) and
        (parent.state.max_days < const.BONUS_2_MAX_DAYS)):
        # Player gets bonus #2
        new_days = const.BONUS_2_MAX_DAYS
        new_store_purchases = parent.state.max_store_purchases_per_day + 1

    if new_days is not None:
        infoDialog(parent, "Congratulations!",
                   "Congratulations, industrious trader! you have accrued {0:,}. Your total "
                   "days have been increased to {1}, and you can now make {2} store "
                   "purchases per day.".format(parent.state.money, new_days, new_store_purchases))

        parent.state.max_days = new_days
        parent.state.max_store_purchases_per_day = new_store_purchases
        parent.infoBar.update()


def _add_wrap(v, a, w):
    return (v + a) % w

def _sub_wrap(v, s, w):
    if s > v:
        return w - (s - v)
    else:
        return v - s


def _iter_bytes(data, byte_func):
    ret = bytearray(data)
    i = 0
    j = 0

    pwd_rounds = 0
    data_rounds = 0

    while (data_rounds < DATA_ITER) and (pwd_rounds < PWD_ITER):
        ret[i] = byte_func(ret[i], PWD[j], 256)

        if i < (len(data) - 1):
            i += 1
        else:
            i = 0
            data_rounds += 1

        if j < (len(PWD) - 1):
            j += 1
        else:
            j = 0
            pwd_rounds += 1

    return data_rounds * pwd_rounds, bytes(ret)

# note: scores_encode is not cryptographically secure by any means. It is
# a simple byte-scrambling function to prevent shared high scores from being
# easily modified, but I'm sure someone who really wanted could easily crack it

def scores_encode(data):
    number, data = _iter_bytes(data, _add_wrap)
    data += b':' + bytes(str(number), encoding='utf8')
    return base64.b64encode(data)

def scores_decode(data):
    string = base64.b64decode(data)
    fields = string.split(b':')
    expected_num = int(fields[-1].decode('utf-8'))
    number, data = _iter_bytes(b':'.join(fields[:-1]), _sub_wrap)
    if number != expected_num:
        return None

    return data
