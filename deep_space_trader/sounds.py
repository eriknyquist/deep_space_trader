import os
from PyQt5.QtMultimedia import QSound, QSoundEffect
from PyQt5.QtCore import QUrl
from deep_space_trader.utils import AUDIO_DIR

class AudioPlayer:

    def __init__(self):
        self.TravelSound = QSoundEffect()
        self.SellSound = QSoundEffect()
        self.WhooshPopSound = QSoundEffect()
        self.ShipUpgradeSound = QSoundEffect()
        self.DeathSound = QSoundEffect()
        self.PlanetDiscoverySound = QSoundEffect()
        self.BattleSound = QSoundEffect()
        self.FailureSound = QSoundEffect()
        self.VictorySound = QSoundEffect()
        self.BattleUpgradeSound = QSoundEffect()
        self.ScoutUpgradeSound = QSoundEffect()
        self.PlanetDestructionSound = QSoundEffect()
        self.TradingConsoleSound = QSoundEffect()
        self.WarehouseTripsUpgradeSound = QSoundEffect()
        self.RumourSound = QSoundEffect()
        self.RumourTrueSound = QSoundEffect()
        self.DumpSound = QSoundEffect()

        self.TravelSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "rocket_launch.wav")))
        self.SellSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "cash_register.wav")))
        self.WhooshPopSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "whoosh_pop.wav")))
        self.ShipUpgradeSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "ship_upgrade.wav")))
        self.DeathSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "death.wav")))
        self.PlanetDiscoverySound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "planet_discovery.wav")))
        self.BattleSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "battle.wav")))
        self.FailureSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "failure.wav")))
        self.VictorySound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "victory.wav")))
        self.BattleUpgradeSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "battle_upgrade.wav")))
        self.ScoutUpgradeSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "scout_upgrade.wav")))
        self.PlanetDestructionSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "planet_destruction.wav")))
        self.TradingConsoleSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "trading_console.wav")))
        self.WarehouseTripsUpgradeSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "warehouse_trips_upgrade.wav")))
        self.RumourSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "rumour.wav")))
        self.RumourTrueSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "rumour_true.wav")))
        self.DumpSound.setSource(QUrl.fromLocalFile(os.path.join(AUDIO_DIR, "dump.wav")))

        self.enabled = True

    def setEnabled(self, enabled):
        self.enabled = enabled

    def play(self, sound):
        if self.enabled:
            sound.play()
