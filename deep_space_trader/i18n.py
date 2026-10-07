import os
import sys

from PyQt5.QtCore import QCoreApplication, QLocale, QTranslator, QLibraryInfo

from deep_space_trader import constants as const

# Found the same way as utils.SOURCE_DIR (utils can't be imported here, since it uses this module)
if getattr(sys, 'frozen', False):
    _SOURCE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    _SOURCE_DIR = os.path.dirname(__file__)

TRANSLATIONS_DIR = os.path.join(_SOURCE_DIR, 'translations')

# Largest count Qt accepts for choosing a plural form (it's a C int)
_INT_MAX = 2147483647


def translate(context, text, disambiguation=None, n=-1):
    """
    Same as QCoreApplication.translate, but also works for counts too big for Qt.

    pylupdate5 only finds strings passed to a function named "translate" (or
    "tr"), and only sees 'n' when it is passed positionally, so always call this
    as translate("Context", "text", None, n) for plurals. The count is shown
    where the text has %Ln (or %n).
    """
    if n > _INT_MAX:
        # Choose the plural form using a smaller stand-in number with the same
        # last six digits (plural rules only depend on the last few digits),
        # then put the real number back in place of the stand-in
        stand_in = (n % 1000000) + 1000000
        ret = QCoreApplication.translate(context, text, disambiguation, stand_in)
        ret = ret.replace(QLocale().toString(stand_in), formatNumber(n))
        return ret.replace(str(stand_in), formatNumber(n))

    return QCoreApplication.translate(context, text, disambiguation, n)


def formatNumber(value):
    """
    Format a whole number for the current locale (e.g. 1,000,000 or 1.000.000)
    """
    return QLocale().toString(int(value))


def formatPercent(value, decimals=0):
    """
    Format a percentage for the current locale (e.g. 12.5% or 12,5 %)
    """
    number = QLocale().toString(float(value), 'f', decimals)
    return translate("Numbers", "{0}%", "a percentage, e.g. 12.5%").format(number)


def joinList(names):
    """
    Join a list of names for use in a sentence, e.g. "A, B and C"
    """
    if len(names) == 1:
        return names[0]

    sep = translate("Lists", ", ", "separator between the items of a list, except the last two")
    return translate("Lists", "{0} and {1}", "joins the last two items of a list, e.g. \"A and B\"").format(
                     sep.join(names[:-1]), names[-1])


def _installTranslator(app, filename, directory, locale=None):
    translator = QTranslator(app)
    if locale is None:
        loaded = translator.load(filename, directory)
    else:
        loaded = translator.load(locale, filename, "_", directory)

    if loaded:
        app.installTranslator(translator)


def installTranslators(app):
    """
    Load translations for the system language, or for constants.FORCE_LANGUAGE
    if it is set. Must be called before any translated text is created.
    """
    if const.FORCE_LANGUAGE is not None:
        # Also makes formatNumber() and %Ln use this language's number format
        QLocale.setDefault(QLocale(const.FORCE_LANGUAGE))

    # Qt's own text, e.g. the Yes/No/Cancel buttons in message boxes
    _installTranslator(app, "qtbase", QLibraryInfo.location(QLibraryInfo.TranslationsPath), QLocale())

    # English plural forms ("1 planet", "2 planets"); also used for any text
    # that the translation for the chosen language doesn't cover
    _installTranslator(app, "deep_space_trader_en", TRANSLATIONS_DIR)

    # Translation for the chosen language. Installed last, so it's used first
    _installTranslator(app, "deep_space_trader", TRANSLATIONS_DIR, QLocale())
