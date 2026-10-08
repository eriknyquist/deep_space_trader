"""
Checks on the translation files in deep_space_trader/translations.

If test_translation_files_are_up_to_date fails, text in the code has changed:
run pylupdate5 on the .ts files (see translation_tasks.md) and translate any new
strings in Qt Linguist.
"""
import collections
import glob
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

import deep_space_trader
from deep_space_trader.i18n import TRANSLATIONS_DIR

PACKAGE_DIR = os.path.dirname(deep_space_trader.__file__)
TS_FILES = sorted(glob.glob(os.path.join(TRANSLATIONS_DIR, "*.ts")))


def messages(ts_file):
    """
    {(context, source, comment): message element} for a .ts file, without obsolete messages
    """
    ret = {}
    root = ET.parse(ts_file).getroot()
    for context in root.iter("context"):
        name = context.find("name").text
        for message in context.findall("message"):
            translation = message.find("translation")
            if translation.get("type") in ("obsolete", "vanished"):
                continue

            comment = message.find("comment")
            key = (name, message.find("source").text, comment.text if comment is not None else None)
            ret[key] = message

    return ret


def forms(message):
    """
    Translated text of a message: a list with one entry, or one entry per plural form
    """
    translation = message.find("translation")
    plural = translation.findall("numerusform")
    if message.get("numerus") == "yes":
        return [f.text or "" for f in plural]

    return [translation.text or ""]


def markers(text):
    """
    The parts of a string that a translation must keep: placeholders and HTML tags
    """
    return (collections.Counter(re.findall(r"\{\d\}", text)),
            "%Ln" in text,
            collections.Counter(re.findall(r"</?[a-z]+>", text)))


def test_translation_files_exist():
    names = [os.path.basename(f) for f in TS_FILES]
    assert "deep_space_trader_en.ts" in names
    assert "deep_space_trader_pt_BR.ts" in names


@pytest.mark.parametrize("ts_file", TS_FILES, ids=os.path.basename)
def test_translation_files_are_up_to_date(ts_file, tmp_path):
    fresh = str(tmp_path / os.path.basename(ts_file))
    shutil.copy(ts_file, fresh)
    sources = sorted(glob.glob(os.path.join(PACKAGE_DIR, "*.py")))
    subprocess.run([sys.executable, "-m", "PyQt5.pylupdate_main"] + sources + ["-ts", fresh],
                   check=True, capture_output=True)

    expected = set(messages(fresh))
    actual = set(messages(ts_file))
    assert sorted(expected - actual) == [], "strings in the code missing from %s" % ts_file
    assert sorted(actual - expected) == [], "strings in %s no longer in the code" % ts_file


@pytest.mark.parametrize("ts_file", TS_FILES, ids=os.path.basename)
def test_translation_files_have_a_language(ts_file):
    language = ET.parse(ts_file).getroot().get("language")
    assert language
    assert os.path.basename(ts_file) == "deep_space_trader_%s.ts" % language


def test_portuguese_translation_is_complete():
    ts_file = os.path.join(TRANSLATIONS_DIR, "deep_space_trader_pt_BR.ts")
    unfinished = [key for key, m in messages(ts_file).items()
                  if m.find("translation").get("type") == "unfinished" or not all(forms(m))]
    assert unfinished == []


@pytest.mark.parametrize("ts_file", TS_FILES, ids=os.path.basename)
def test_translations_keep_placeholders_and_tags(ts_file):
    wrong = []
    for (context, source, comment), message in messages(ts_file).items():
        for text in forms(message):
            if text and markers(text) != markers(source):
                wrong.append((context, source, text))

    assert wrong == []


@pytest.mark.parametrize("ts_file", TS_FILES, ids=os.path.basename)
def test_plurals_have_two_forms(ts_file):
    # English and Brazilian Portuguese both have a singular and a plural form
    for key, message in messages(ts_file).items():
        if message.get("numerus") == "yes":
            assert len(forms(message)) == 2, key
            assert all(forms(message)), key


def test_english_file_only_translates_plurals():
    ts_file = os.path.join(TRANSLATIONS_DIR, "deep_space_trader_en.ts")
    for key, message in messages(ts_file).items():
        if message.get("numerus") != "yes":
            assert forms(message) == [""], key
