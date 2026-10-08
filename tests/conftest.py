"""
Shared test setup.

Every test runs headless (QT_QPA_PLATFORM=offscreen), with sounds replaced by a
silent stand-in, with the config file (high scores) redirected to a temporary
file, and with English number formatting. Message boxes are recorded instead of
shown (see the 'dialogs' fixture), so tests never block waiting for a click.
"""
import gc
import importlib
import os
import sys
import traceback
import types

# Must be set before Qt is loaded
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt5 import QtWidgets, QtCore

from helpers import FakeAudio

try:
    importlib.import_module("deep_space_trader.sounds")
except ImportError:
    # QtMultimedia can't be loaded (e.g. no audio libraries on a build server).
    # Nothing outside test_sounds.py needs the real module
    sys.modules["deep_space_trader.sounds"] = types.SimpleNamespace(
        AudioPlayer=FakeAudio, waitForSounds=lambda parent, audio: None)

from deep_space_trader import config  # noqa: E402
from deep_space_trader import constants as const  # noqa: E402
from deep_space_trader import (  # noqa: E402
    main_widget, store, item_browsers, transaction_dialogs, location_browser,
    location_picker, top_button_bar, high_scores, utils
)

# Modules that import the dialog functions by name, and so must be patched one by one
DIALOG_MODULES = [main_widget, store, item_browsers, transaction_dialogs, location_browser,
                  location_picker, top_button_bar, high_scores, config, utils]


@pytest.fixture(scope="session")
def qapp():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture(autouse=True)
def isolated(qapp, tmp_path, monkeypatch):
    """
    Keep tests away from the real config file, and use English number formatting
    """
    monkeypatch.setattr(config, "FILENAME", str(tmp_path / "config.json"))
    monkeypatch.setitem(config.config, config.SCORES_KEY, [])
    monkeypatch.setitem(config.config, config.SHOWINTRO_KEY, True)

    old_locale = QtCore.QLocale()
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates))
    yield
    QtCore.QLocale.setDefault(old_locale)


@pytest.fixture(autouse=True)
def fail_on_errors_in_qt_code(monkeypatch):
    """
    Fail the test if an exception is raised in code that Qt calls (e.g. a
    keyPressEvent or a button's slot). PyQt5 only prints these, so without this
    a test could pass while the game hit an error
    """
    errors = []
    monkeypatch.setattr(sys, "excepthook", lambda *exc_info: errors.append(exc_info))
    yield
    if errors:
        pytest.fail("Exception raised in code called by Qt:\n" +
                    "".join("".join(traceback.format_exception(*e)) for e in errors))


class Dialogs(object):
    """
    Records message boxes and dialogs instead of showing them.

    Yes/no questions are answered True unless 'answers' has an entry whose key
    appears in the dialog's title (e.g. answers["pirate"] = False). Names
    entered in QInputDialog.getText are taken from 'names'. A dialog opened
    with exec_() returns straight away, after calling 'on_exec' with it if set
    (e.g. to pick planets in the planet destruction dialog)
    """
    def __init__(self):
        self.shown = []        # (kind, title, message)
        self.executed = []     # dialogs whose exec_() was called
        self.answers = {}
        self.names = []
        self.on_exec = None

    def yesNo(self, parent, header="", message=None, cancelable=True):
        self.shown.append(("question", header, message or ""))
        for key, answer in self.answers.items():
            if key in header:
                return answer

        return True

    def info(self, parent, heading="", message=""):
        self.shown.append(("info", heading, message))

    def error(self, parent, heading=None, message=None):
        self.shown.append(("error", heading or "", message or ""))

    def messages(self, kind=None):
        return [m for k, t, m in self.shown if kind is None or k == kind]

    def titles(self, kind=None):
        return [t for k, t, m in self.shown if kind is None or k == kind]

    def clear(self):
        self.shown.clear()
        self.executed.clear()


@pytest.fixture
def dialogs(monkeypatch):
    d = Dialogs()
    for module in DIALOG_MODULES:
        for name, func in (("yesNoDialog", d.yesNo), ("infoDialog", d.info), ("errorDialog", d.error)):
            if hasattr(module, name):
                monkeypatch.setattr(module, name, func)

    def exec_(dialog):
        d.executed.append(dialog)
        if d.on_exec is not None:
            d.on_exec(dialog)
        return 0

    monkeypatch.setattr(QtWidgets.QDialog, "exec_", exec_)

    def getText(parent, title, label, *args, **kwargs):
        d.shown.append(("input", title, label))
        if d.names:
            return d.names.pop(0), True

        return "", False

    monkeypatch.setattr(QtWidgets.QInputDialog, "getText", staticmethod(getText))
    return d


@pytest.fixture
def game(qapp, dialogs, monkeypatch):
    """
    A new game in a shown main window, with plenty of money and no random
    rumours. Returns the MainWidget;
    the game state is game.state, and played sounds are in game.audio.played
    """
    monkeypatch.setattr(main_widget, "AudioPlayer", FakeAudio)

    # No random rumours when a day passes (the rumour tests turn them back on)
    monkeypatch.setattr(const, "CHANCE_TRADING_TIP_PERCENTAGE", 0.0)

    from deep_space_trader.__main__ import MainWindow

    window = MainWindow(qapp.primaryScreen())
    window.show()
    qapp.processEvents()

    widget = window.widget
    widget.state.money = 10 ** 9
    widget.infoBar.update()
    dialogs.clear()

    yield widget

    # Delete the window now, rather than leaving it for Python's garbage collector,
    # which can crash when it frees Qt widgets in the middle of a later test
    window.hide()
    window.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)
    gc.collect()
