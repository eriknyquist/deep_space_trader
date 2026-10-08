import json
import html

import pytest
from PyQt5 import QtCore

from deep_space_trader import config
from deep_space_trader import constants as const
from deep_space_trader.high_scores import HighScoreTable, HighScoreSharing, validScores
from deep_space_trader.utils import scores_encode


def share_string(scores):
    return scores_encode(bytes(json.dumps(scores), encoding="utf8")).decode("utf-8")


@pytest.mark.parametrize("scores", [
    [],
    [["Bob", 1000]],
    [["Bob", 1000], ["x" * const.MAX_HIGHSCORE_NAME_LEN, 0]],
])
def test_valid_scores(scores):
    assert validScores(scores)


@pytest.mark.parametrize("scores", [
    None,
    {"Bob": 1000},
    "Bob",
    [["Bob", "lots"]],
    [["Bob", 5, 1]],
    [["Bob"]],
    [[5, 5]],
    [["Bob", 1.5]],
    [["Bob", True]],
    [["Bob", -1]],
    [["x" * (const.MAX_HIGHSCORE_NAME_LEN + 1), 5]],
])
def test_invalid_scores(scores):
    assert not validScores(scores)


def test_high_scores_are_sorted_and_limited():
    for i in range(const.MAX_HIGH_SCORES + 3):
        config.add_highscore("player%d" % i, i * 100)

    scores = config.get_highscores()
    assert len(scores) == const.MAX_HIGH_SCORES
    assert [s for _, s in scores] == sorted((s for _, s in scores), reverse=True)
    assert scores[0] == ["player%d" % (const.MAX_HIGH_SCORES + 2), (const.MAX_HIGH_SCORES + 2) * 100]


def test_config_store_and_load(dialogs):
    config.add_highscore("Bob", 1000)
    config.set_show_intro(False)
    config.config_store()

    config.config[config.SCORES_KEY] = []
    config.config[config.SHOWINTRO_KEY] = True
    config.config_load()
    assert config.get_highscores() == [["Bob", 1000]]
    assert config.get_show_intro() is False
    assert dialogs.shown == []


def test_config_file_is_scrambled():
    config.add_highscore("Bob", 1000)
    config.config_store()
    with open(config.FILENAME) as fh:
        assert "Bob" not in fh.read()


def test_malformed_config_file_shows_error(dialogs):
    with open(config.FILENAME, "w") as fh:
        fh.write("not json")

    config.config_load()
    assert dialogs.titles("error") == ["Error"]
    assert config.get_highscores() == []


def test_sharing_adds_valid_scores(dialogs):
    sharing = HighScoreSharing(None)
    sharing.inputScores.setText(share_string([["Bob", 1000], ["Al", 5]]))
    sharing.inputButtonClicked()

    assert sorted(config.get_highscores()) == [["Al", 5], ["Bob", 1000]]
    assert "Bob (1,000)" in dialogs.messages("question")[0]
    assert dialogs.titles("info") == ["Success"]


def test_sharing_can_be_declined(dialogs):
    dialogs.answers["Add scores?"] = False
    sharing = HighScoreSharing(None)
    sharing.inputScores.setText(share_string([["Bob", 1000]]))
    sharing.inputButtonClicked()
    assert config.get_highscores() == []


@pytest.mark.parametrize("scores", [
    [["Bob", "lots"]],
    [["Bob", 5, 1]],
    {"a": 1},
    [["<font size=7>" + "x" * 40, 5]],
])
def test_sharing_rejects_invalid_scores(dialogs, scores):
    sharing = HighScoreSharing(None)
    sharing.inputScores.setText(share_string(scores))
    sharing.inputButtonClicked()

    assert dialogs.messages("error") == ["Failed to decode high scores"]
    assert config.get_highscores() == []


def test_sharing_rejects_garbage(dialogs):
    sharing = HighScoreSharing(None)
    sharing.inputScores.setText("not a high score string")
    sharing.inputButtonClicked()
    assert dialogs.messages("error") == ["Failed to decode high scores"]


def test_sharing_shows_names_as_plain_text(dialogs):
    sharing = HighScoreSharing(None)
    sharing.inputScores.setText(share_string([["<b>Bob</b>", 1]]))
    sharing.inputButtonClicked()
    assert html.escape("<b>Bob</b>") in dialogs.messages("question")[0]


def test_sharing_shows_own_scores():
    config.add_highscore("Bob", 1000)
    sharing = HighScoreSharing(None)
    decoded = sharing.displayScores.toPlainText()
    assert decoded == share_string(config.get_highscores())


def test_high_score_table():
    for name, score in (("Al", 5), ("<b>Bob</b>", 1000), ("Cy", 50), ("Di", 1)):
        config.add_highscore(name, score)

    dialog = HighScoreTable(None)
    table = dialog.table
    labels = [table.cellWidget(row, 0) for row in range(table.rowCount())]
    assert [l.text() for l in labels] == [
        "&lt;b&gt;Bob&lt;/b&gt; <i><b>(1st place)</b></i>",
        "Cy <i><b>(2nd place)</b></i>",
        "Al <i><b>(3rd place)</b></i>",
        "Di",
    ]
    assert all(l.textFormat() == QtCore.Qt.RichText for l in labels)
    assert [table.item(row, 1).text() for row in range(table.rowCount())] == ["1,000", "50", "5", "1"]
