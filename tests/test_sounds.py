import ast
import glob
import os
import re

import pytest

import deep_space_trader
from deep_space_trader import sounds
from deep_space_trader.utils import AUDIO_DIR

PACKAGE_DIR = os.path.dirname(deep_space_trader.__file__)

# conftest.py replaces the sounds module with a stand-in when QtMultimedia can't be loaded
HAVE_QTMULTIMEDIA = hasattr(sounds, "SoundLoadingDialog")


def sound_files():
    """
    sounds.SOUND_FILES, read from the source so that this works without QtMultimedia
    """
    with open(os.path.join(PACKAGE_DIR, "sounds.py")) as fh:
        tree = ast.parse(fh.read())

    for node in tree.body:
        if isinstance(node, ast.Assign) and node.targets[0].id == "SOUND_FILES":
            return ast.literal_eval(node.value)

    raise AssertionError("SOUND_FILES not found")


def test_every_sound_file_exists():
    for filename in sound_files().values():
        assert os.path.isfile(os.path.join(AUDIO_DIR, filename)), filename


def test_every_sound_played_is_defined():
    # The tests use a silent stand-in that accepts any sound name, so check
    # the names used in the code against the real list
    used = set()
    for path in glob.glob(os.path.join(PACKAGE_DIR, "*.py")):
        with open(path) as fh:
            used |= set(re.findall(r"\baudio\.(\w+Sound)\b", fh.read()))

    assert used
    assert used <= set(sound_files())


@pytest.mark.skipif(not HAVE_QTMULTIMEDIA, reason="QtMultimedia isn't available")
def test_audio_player(qapp):
    player = sounds.AudioPlayer()
    try:
        assert player.totalCount == len(sound_files())
        for name in sound_files():
            assert getattr(player, name) == name

        player.setEnabled(False)
        player.play(player.TravelSound)
    finally:
        player.stop()

    assert all(label.endswith("...") for label in sounds.SoundLoadingDialog.LABEL_STRINGS)
