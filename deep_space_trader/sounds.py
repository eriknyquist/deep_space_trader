import os
from PyQt5.QtMultimedia import QSound
from deep_space_trader.utils import AUDIO_DIR

class AudioPlayer:
    TravelSound = QSound(os.path.join(AUDIO_DIR, "rocket_launch.wav"))
    SellSound = QSound(os.path.join(AUDIO_DIR, "cash_register.wav"))
    WhooshPopSound = QSound(os.path.join(AUDIO_DIR, "whoosh_pop.wav"))
    ShipUpgradeSound = QSound(os.path.join(AUDIO_DIR, "ship_upgrade.wav"))
    DeathSound = QSound(os.path.join(AUDIO_DIR, "death.wav"))
    PlanetDiscoverySound = QSound(os.path.join(AUDIO_DIR, "planet_discovery.wav"))
    BattleSound = QSound(os.path.join(AUDIO_DIR, "battle.wav"))
    FailureSound = QSound(os.path.join(AUDIO_DIR, "failure.wav"))
    VictorySound = QSound(os.path.join(AUDIO_DIR, "victory.wav"))

    def __init__(self):
        self.enabled = True

    def setEnabled(self, enabled):
        self.enabled = enabled

    def play(self, sound):
        if self.enabled:
            sound.play()
