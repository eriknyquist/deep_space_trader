import random
import types

import pytest
from PyQt5 import QtWidgets, QtCore

from deep_space_trader import constants as const
from deep_space_trader import utils
from deep_space_trader.game_state import State


def test_percent_chance_extremes():
    random.seed(20)
    assert not any(utils.percentChance(0) for _ in range(1000))
    assert all(utils.percentChance(100) for _ in range(1000))


def test_percent_chance_is_accurate():
    # Bug 10: rolls used randint(0, 100), which has 101 outcomes
    random.seed(21)
    hits = sum(utils.percentChance(20) for _ in range(100000))
    assert 19500 < hits < 20500


@pytest.fixture
def bonus_parent():
    random.seed(22)
    updates = []
    return types.SimpleNamespace(state=State(None),
                                 infoBar=types.SimpleNamespace(update=lambda: updates.append(1)),
                                 updates=updates)


def test_no_money_bonus_below_the_first_threshold(bonus_parent, dialogs):
    bonus_parent.state.money = const.BONUS_1_MONEY - 1
    utils.checkForMoneyBonus(bonus_parent)
    assert bonus_parent.state.max_days == const.INITIAL_MAX_DAYS
    assert dialogs.shown == []


def test_first_money_bonus(bonus_parent, dialogs):
    state = bonus_parent.state
    state.money = const.BONUS_1_MONEY
    utils.checkForMoneyBonus(bonus_parent)
    assert state.max_days == const.BONUS_1_MAX_DAYS
    assert state.max_store_purchases_per_day == const.MAX_STORE_PURCHASES_PER_DAY + 1
    assert dialogs.titles() == ["Congratulations!"]
    assert bonus_parent.updates

    # Only given once
    utils.checkForMoneyBonus(bonus_parent)
    assert state.max_store_purchases_per_day == const.MAX_STORE_PURCHASES_PER_DAY + 1
    assert len(dialogs.shown) == 1


def test_both_money_bonuses_at_once(bonus_parent, dialogs):
    # Bug 11: reaching both at once used to give only one extra purchase
    state = bonus_parent.state
    state.money = const.BONUS_2_MONEY
    utils.checkForMoneyBonus(bonus_parent)
    assert state.max_days == const.BONUS_2_MAX_DAYS
    assert state.max_store_purchases_per_day == const.MAX_STORE_PURCHASES_PER_DAY + 2
    assert "you can now make 6 store purchases per day" in dialogs.messages()[0]


def test_money_bonuses_one_after_the_other(bonus_parent, dialogs):
    state = bonus_parent.state
    state.money = const.BONUS_1_MONEY
    utils.checkForMoneyBonus(bonus_parent)
    state.money = const.BONUS_2_MONEY
    utils.checkForMoneyBonus(bonus_parent)
    assert state.max_days == const.BONUS_2_MAX_DAYS
    assert state.max_store_purchases_per_day == const.MAX_STORE_PURCHASES_PER_DAY + 2


def test_scores_encode_round_trip():
    data = b'[["Bob", 1000], ["Al", 5]]'
    assert utils.scores_decode(utils.scores_encode(data)) == data


def test_scores_decode_rejects_tampered_data():
    import base64
    encoded = base64.b64decode(utils.scores_encode(b'[["Bob", 1000]]'))
    data, number = encoded.rsplit(b":", 1)
    tampered = base64.b64encode(data + b":" + str(int(number) + 1).encode())
    assert utils.scores_decode(tampered) is None


def make_table(keys):
    table = QtWidgets.QTableWidget(len(keys), 1)
    for row, (text, key) in enumerate(keys):
        item = QtWidgets.QTableWidgetItem(text)
        if key is not None:
            item.setData(QtCore.Qt.UserRole, key)
        table.setItem(row, 0, item)
    return table


def test_row_key_prefers_stored_key_over_text():
    table = make_table([("estanho", "tin"), ("plain", None)])
    assert utils.rowKey(table, 0) == "tin"
    assert utils.rowKey(table, 1) == "plain"


def test_select_row_by_key():
    table = make_table([("a", "tin"), ("b", "gold"), ("c", "silver")])
    assert utils.selectedRowKey(table) is None

    utils.selectRowByKey(table, "silver")
    assert table.currentRow() == 2
    assert utils.selectedRowKey(table) == "silver"

    utils.selectRowByKey(table, "missing")
    assert table.currentRow() == 2
