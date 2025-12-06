import os
from PyQt5.QtMultimedia import QSound
from deep_space_trader.utils import AUDIO_DIR

class AudioPlayer:
    TravelSound = QSound(os.path.join(AUDIO_DIR, "rocket_launch.wav"))
    SellSound = QSound(os.path.join(AUDIO_DIR, "cash_register.wav"))
    BuySound = QSound(os.path.join(AUDIO_DIR, "whoosh_pop.wav"))

    def __init__(self):
        self.enabled = True

    def setEnabled(self, enabled):
        self.enabled = enabled

    def play(self, sound):
        if self.enabled:
            sound.play()
