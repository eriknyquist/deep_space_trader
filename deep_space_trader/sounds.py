import os
import random
from PyQt5.QtMultimedia import QAudioDeviceInfo, QSoundEffect
from PyQt5.QtCore import QUrl, QObject, QThread, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QDialog, QProgressDialog
from deep_space_trader.utils import AUDIO_DIR

# AudioPlayer attribute name -> sound file
SOUND_FILES = {
    "TravelSound": "rocket_launch.wav",
    "SellSound": "cash_register.wav",
    "WhooshPopSound": "whoosh_pop.wav",
    "ShipUpgradeSound": "ship_upgrade.wav",
    "DeathSound": "death.wav",
    "PlanetDiscoverySound": "planet_discovery.wav",
    "BattleSound": "battle.wav",
    "FailureSound": "failure.wav",
    "VictorySound": "victory.wav",
    "BattleUpgradeSound": "battle_upgrade.wav",
    "ScoutUpgradeSound": "scout_upgrade.wav",
    "PlanetDestructionSound": "planet_destruction.wav",
    "TradingConsoleSound": "trading_console.wav",
    "WarehouseTripsUpgradeSound": "warehouse_trips_upgrade.wav",
    "RumourSound": "rumour.wav",
    "RumourTrueSound": "rumour_true.wav",
    "DumpSound": "dump.wav",
}


class _SoundEffects(QObject):
    """
    Owns the QSoundEffect objects, and lives in the audio thread.

    On Windows, looking up the default audio output device takes ~0.5s. A
    QSoundEffect created without a device repeats that lookup when its sample
    has loaded, so the device is looked up once here and passed to every
    effect, which brings each one down to a few milliseconds.
    """
    # Number of sounds that have finished loading (successfully or not)
    loadProgress = pyqtSignal(int)

    def __init__(self):
        super(_SoundEffects, self).__init__()
        self.effects = {}
        self.finished = set()

    @pyqtSlot()
    def load(self):
        device = QAudioDeviceInfo.defaultOutputDevice()

        for name, filename in SOUND_FILES.items():
            effect = QSoundEffect(device, self)
            self.effects[name] = effect
            effect.statusChanged.connect(lambda name=name: self.checkStatus(name))
            effect.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, filename)))
            self.checkStatus(name)

    def checkStatus(self, name):
        if name in self.finished:
            return

        # A sound that failed to load still counts as finished, so that the
        # loading dialog can't get stuck waiting for it
        if self.effects[name].status() in (QSoundEffect.Ready, QSoundEffect.Error):
            self.finished.add(name)
            self.loadProgress.emit(len(self.finished))

    @pyqtSlot(str)
    def play(self, name):
        # If the sound hasn't finished loading yet, QSoundEffect plays it once ready
        self.effects[name].play()


class AudioPlayer(QObject):
    _playRequested = pyqtSignal(str)

    # Number of sounds loaded so far, and total number of sounds
    loadProgress = pyqtSignal(int, int)

    def __init__(self):
        super(AudioPlayer, self).__init__()

        # Sounds are referred to by name, e.g. audio.play(audio.TravelSound)
        for name in SOUND_FILES:
            setattr(self, name, name)

        self.enabled = True
        self.loadedCount = 0
        self.totalCount = len(SOUND_FILES)

        self._thread = QThread()
        self._thread.setObjectName("AudioThread")
        self._effects = _SoundEffects()
        self._effects.moveToThread(self._thread)
        self._thread.started.connect(self._effects.load)
        self._playRequested.connect(self._effects.play)
        self._effects.loadProgress.connect(self._onLoadProgress)
        QApplication.instance().aboutToQuit.connect(self.stop)
        self._thread.start()

    @pyqtSlot(int)
    def _onLoadProgress(self, count):
        self.loadedCount = count
        self.loadProgress.emit(count, self.totalCount)

    def allLoaded(self):
        return self.loadedCount >= self.totalCount

    def stop(self):
        self._thread.quit()
        self._thread.wait()

    def setEnabled(self, enabled):
        self.enabled = enabled

    def play(self, sound):
        if self.enabled:
            self._playRequested.emit(sound)


class SoundLoadingDialog(QProgressDialog):
    """
    Modal progress dialog shown over the main window until all sounds have
    loaded, so the game can't be played with sounds missing or playing late.
    It can't be cancelled or closed by the player.
    """
    # Give up waiting after this long, in case a sound never finishes loading
    TIMEOUT_MS = 30000

    # Label text cycles through these, moving to the next one after a randomly
    # chosen number of progress updates (see LABEL_UPDATE_COUNTS), and wrapping
    # around to the start after the last one
    LABEL_STRINGS = [
        "reserializing quantum encoders",
        "backtracing core entanglements",
        "reverse-engineering universe",
        "rotating atomic stack carriers",
        "initializing reality",
        "deriving orbital constants",
        "rate-matching baffle alignments"]

    # Number of progress updates to wait before changing the label is picked
    # at random from this list each time, so the changes look less mechanical
    LABEL_UPDATE_COUNTS = [1, 2, 3, 4]

    def __init__(self, parent, audio):
        super(SoundLoadingDialog, self).__init__(parent)

        self.audio = audio
        self.loadingDone = False
        self.updatesUntilNextLabel = random.choice(self.LABEL_UPDATE_COUNTS)

        self.setWindowTitle("Please wait")
        self.setLabelText(random.choice(self.LABEL_STRINGS))
        self.setCancelButton(None)
        self.setRange(0, audio.totalCount)
        self.setMinimumDuration(0)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        audio.loadProgress.connect(self.onLoadProgress)
        self.setValue(audio.loadedCount)
        QTimer.singleShot(self.TIMEOUT_MS, self.finish)

    def onLoadProgress(self, count, total):
        self.updatesUntilNextLabel -= 1
        if self.updatesUntilNextLabel <= 0:
            self.setLabelText(random.choice(self.LABEL_STRINGS) + "...")
            self.updatesUntilNextLabel = random.choice(self.LABEL_UPDATE_COUNTS)

        self.setValue(count)
        if count >= total:
            self.finish()

    def finish(self):
        if not self.loadingDone:
            self.loadingDone = True
            self.audio.loadProgress.disconnect(self.onLoadProgress)
            self.done(QDialog.Accepted)

    def reject(self):
        # Ignore the Escape key
        pass

    def closeEvent(self, event):
        if not self.loadingDone:
            event.ignore()


def waitForSounds(parent, audio):
    if not audio.allLoaded():
        dialog = SoundLoadingDialog(parent, audio)
        dialog.exec_()
        dialog.deleteLater()
