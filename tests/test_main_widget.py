import pytest
from PyQt5 import QtWidgets

from deep_space_trader import config
from deep_space_trader import constants as const
from deep_space_trader import main_widget, utils
from deep_space_trader import __version__ as version
from deep_space_trader.high_scores import HighScoreTable
from deep_space_trader.utils import InfoDialog


@pytest.fixture
def rolls(monkeypatch):
    """
    Results for the next percentChance() calls in main_widget, in order
    """
    results = []
    monkeypatch.setattr(main_widget, "percentChance", lambda percent: results.pop(0))
    return results


def start_rumour(game, rolls, increase):
    rolls[:] = [True, increase]
    game.runRandomNotifications()
    # Make the rumour about the current planet, so its outcome is shown
    _, itemname, increase = game.pending_price_anomaly
    game.pending_price_anomaly = (game.state.current_planet, next(iter(game.state.current_planet.items.items)),
                                  increase)
    return itemname


@pytest.mark.parametrize("increase, word", [(True, "expensive"), (False, "cheap")])
def test_rumour_message(game, dialogs, rolls, increase, word):
    rolls[:] = [True, increase]
    game.runRandomNotifications()
    planet, itemname, pending_increase = game.pending_price_anomaly
    assert pending_increase == increase

    sentences = ["You hear a rumour that %s will be %s %s on %s tomorrow!" % (itemname, adverb, word, planet.full_name)
                 for adverb in ("very", "extremely", "unreasonably", "unusually")]
    assert dialogs.titles("info") == ["Rumour overheard!"]
    assert dialogs.messages("info")[0] in sentences
    assert game.audio.played == ["RumourSound"]


def test_no_rumour_most_days(game, dialogs, rolls):
    rolls[:] = [False]
    game.runRandomNotifications()
    assert game.pending_price_anomaly is None
    assert dialogs.shown == []


@pytest.mark.parametrize("increase, low, high, text", [
    (True, 3.0, 6.0, "through the roof"),
    (False, 0.05, 0.2, "at an all-time low"),
])
def test_true_rumour_changes_price_for_a_day(game, dialogs, rolls, increase, low, high, text):
    start_rumour(game, rolls, increase)
    planet, itemname, _ = game.pending_price_anomaly
    dialogs.clear()

    rolls[:] = [True]
    game.runRandomNotifications()
    item = planet.items.items[itemname]
    old_value = game.temporary_price_change[2]
    assert low * old_value - 1 <= item.value <= high * old_value + 1
    assert dialogs.messages("info") == ["The rumour you heard about %s was true!<br><br>%s prices are %s." % (
        itemname, itemname, text)]

    # The next day, the price goes back to normal
    rolls[:] = [False]
    game.runRandomNotifications()
    assert item.value == old_value
    assert game.temporary_price_change is None


def test_false_rumour(game, dialogs, rolls):
    start_rumour(game, rolls, True)
    planet, itemname, _ = game.pending_price_anomaly
    value = planet.items.items[itemname].value
    dialogs.clear()

    rolls[:] = [False]
    game.runRandomNotifications()
    assert planet.items.items[itemname].value == value
    assert dialogs.messages("info") == ["The rumour you heard about %s on %s was false!" % (itemname, planet.full_name)]


def test_starving_to_death(game, dialogs):
    state = game.state
    state.money = 0
    state.health = 15
    game.advanceDay()
    assert dialogs.messages("info") == ["You have starved to death."]
    # A new game has started
    assert state.day == 1
    assert state.health == 100


def test_end_of_game_high_score(game, dialogs):
    state = game.state
    state.day = state.max_days
    state.money = 123456
    dialogs.names = ["x" * (const.MAX_HIGHSCORE_NAME_LEN + 1), "Bob"]

    game.advanceDay()
    assert dialogs.messages("info") == ["Time is up!"]
    assert "You have achieved a high score (123,456)" in dialogs.messages("question")[0]
    assert dialogs.messages("error") == ["Name is too long (max %d characters)" % const.MAX_HIGHSCORE_NAME_LEN]
    assert config.get_highscores() == [["Bob", 123456]]
    assert [type(d) for d in dialogs.executed] == [HighScoreTable]
    assert state.day == 1


def test_high_score_name_can_be_skipped(game, dialogs):
    game.state.money = 5000
    game.checkHighScore()
    assert config.get_highscores() == []


def test_no_high_score_with_no_money(game, dialogs):
    game.state.money = 0
    game.checkHighScore()
    assert dialogs.shown == []


def test_no_high_score_below_a_full_table(game, dialogs):
    for i in range(const.MAX_HIGH_SCORES):
        config.add_highscore("p%d" % i, 1000 + i)

    game.state.money = 1000
    game.checkHighScore()
    assert dialogs.shown == []


def test_reset_starts_a_new_game(game, dialogs):
    state = game.state
    old_planets = list(state.planets)
    state.day = 12
    state.money = 5
    state.items.remove_all_items()

    game.buttonBar.resetButtonClicked()
    assert state.day == 1
    assert state.money == const.INITIAL_MONEY
    assert not set(map(id, state.planets)) & set(map(id, old_planets))
    assert game.locationBrowser.table.rowCount() == const.INITIAL_PLANET_COUNT
    assert game.infoBar.dayLabel.text() == "1/%d" % const.INITIAL_MAX_DAYS


def test_next_day_button(game):
    game.buttonBar.dayButtonClicked()
    assert game.state.day == 2
    assert game.infoBar.dayLabel.text() == "2/%d" % game.state.max_days


def test_menu_shortcuts_are_unique(game):
    # Bug 1: Ctrl+H was used for both "About" and "Sounds"
    actions = game.main.findChildren(QtWidgets.QAction)
    shortcuts = [a.shortcut().toString() for a in actions if not a.shortcut().isEmpty()]
    assert len(shortcuts) == 11
    assert len(set(shortcuts)) == len(shortcuts)


def test_menu_windows(game, dialogs):
    game.showPrices()
    game.showTravelLog()
    game.showTransactionLog()
    game.shareHighScores()
    assert [type(d).__name__ for d in dialogs.executed] == [
        "PricesTable", "ScrollableTextDisplay", "ScrollableTextDisplay", "HighScoreSharing"]

    prices = dialogs.executed[0].table
    assert prices.rowCount() == 13


def test_sounds_can_be_turned_off(game):
    game.enableSounds(False)
    game.buttonBar.dayButtonClicked()
    game.warehouseItemBrowser.dumpAllButtonClicked()
    assert game.audio.played == []


def test_about_and_intro(dialogs):
    utils.showAboutDialog()
    about = dialogs.executed[-1]
    assert isinstance(about, InfoDialog)
    assert about.text.text().startswith("Deep Space Trader %s<br><br>The year is 5208" % version)
    assert "Created by" in about.text.text()

    assert utils.gameStoryDialog() is False
