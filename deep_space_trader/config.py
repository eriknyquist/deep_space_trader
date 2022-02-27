import os
import json

from deep_space_trader.utils import errorDialog, scores_encode, scores_decode


FILENAME = os.path.join(os.path.expanduser('~'), '.deep_space_trader_config.json')


SCORES_KEY = 'highscores'
SHOWINTRO_KEY = 'show_intro'

config = {
    SHOWINTRO_KEY: True,
    SCORES_KEY: []
}


def _malformed_config():
    errorDialog(None, "Error", message="Malformed config file: %s" % FILENAME)


def config_load():
    if not os.path.isfile(FILENAME):
        return

    try:
        with open(FILENAME, 'r') as fh:
            loaded = json.load(fh)
    except:
        _malformed_config()
        return

    try:
        config[SHOWINTRO_KEY] = loaded[SHOWINTRO_KEY]

        if loaded[SCORES_KEY] == '':
            config[SCORES_KEY] = []
        else:
            data = scores_decode(loaded[SCORES_KEY]).decode('utf-8')
            config[SCORES_KEY] = json.loads(data)
    except:
        _malformed_config()
        return

def config_store():
    cfg = {}

    if config[SCORES_KEY]:
        string = json.dumps(config[SCORES_KEY])
        encoded = scores_encode(bytes(string, encoding='utf8')).decode('utf-8')
    else:
        encoded = ''

    cfg[SCORES_KEY] = encoded
    cfg[SHOWINTRO_KEY] = config[SHOWINTRO_KEY]

    try:
        with open(FILENAME, 'w') as fh:
            json.dump(cfg, fh)
    except:
        errorDialog(None, "Error", message="Unable to write file %s" % FILENAME)

def set_show_intro(value):
    config[SHOWINTRO_KEY] = value

def get_show_intro():
    return config[SHOWINTRO_KEY]

def add_highscore(name, score):
    config[SCORES_KEY].append([name, score])
    config[SCORES_KEY].sort(key=lambda x: x[1])
    config[SCORES_KEY].reverse()

def get_highscores():
    return config[SCORES_KEY]
