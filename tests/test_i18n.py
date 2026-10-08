from PyQt5 import QtCore

from deep_space_trader import constants as const
from deep_space_trader import i18n


def test_format_number_follows_locale():
    assert i18n.formatNumber(1234567) == "1,234,567"
    QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.German, QtCore.QLocale.Germany))
    assert i18n.formatNumber(1234567) == "1.234.567"


def test_format_number_handles_large_numbers():
    assert i18n.formatNumber(10 ** 15) == "1,000,000,000,000,000"


def test_format_percent():
    assert i18n.formatPercent(12.345, 1) == "12.3%"
    assert i18n.formatPercent(-50) == "-50%"


def test_join_list():
    assert i18n.joinList(["A"]) == "A"
    assert i18n.joinList(["A", "B"]) == "A and B"
    assert i18n.joinList(["A", "B", "C", "D"]) == "A, B, C and D"


def test_plural_count_is_substituted():
    assert i18n.translate("Test", "%Ln days remaining", None, 3) == "3 days remaining"
    assert i18n.translate("Test", "%Ln items", None, 1234) == "1,234 items"


def test_plural_count_too_big_for_qt():
    # Qt only accepts counts that fit in a C int; item counts can be larger
    text = i18n.translate("Test", "retrieve %Ln items? (%Ln)", None, 50 * 10 ** 9 + 7)
    assert text == "retrieve 50,000,000,007 items? (50,000,000,007)"


def test_forced_language_sets_number_format(qapp, monkeypatch):
    monkeypatch.setattr(const, "FORCE_LANGUAGE", "pt_BR")
    i18n.installTranslators(qapp)
    try:
        assert i18n.formatNumber(2000000000) == "2.000.000.000"
    finally:
        for translator in qapp.findChildren(QtCore.QTranslator):
            qapp.removeTranslator(translator)
            translator.deleteLater()
