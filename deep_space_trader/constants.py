from deep_space_trader import __maintainer__ as package_author
from deep_space_trader import __email__ as author_email
from deep_space_trader import __name__ as package_name
from deep_space_trader import __version__ as package_version


# ------ Initial values for player data on day 1 ------
INITIAL_MONEY = 2000
INITIAL_TRAVEL_COST = 100
INITIAL_ITEM_CAPACITY = 100
INITIAL_PLANET_COUNT = 8
INITIAL_MAX_DAYS = 30

BONUS_1_MAX_DAYS = 35
BONUS_2_MAX_DAYS = 40

BONUS_1_MONEY = 1000000000
BONUS_2_MONEY = 100000000000

# ------ Base prices for trade items ------

# Common items
PRICE_TIN = 10
PRICE_STEEL = 10
PRICE_COPPER = 15
PRICE_SILVER = 15

# Medium-rare items
PRICE_GOLD = 20
PRICE_SILICON = 25
PRICE_URANIUM = 35
PRICE_DIAMOND = 50
PRICE_TRITIUM = 75
PRICE_PLATINUM = 75
PRICE_PLUTONIUM = 90

# Rare items
PRICE_JADESTONE = 180
PRICE_ANTIMATTER = 200


# ----- Quantity ranges for trade items in each rarity class -----

# Generated common items will always have a quantity value in this range
COMMON_QUANTITY_RANGE = (1000, 100000)

# Generated medium rare items will always have a quantity value in this range
MEDIUM_RARE_QUANTITY_RANGE = (1000, 10000)

# Generated rare items will always have a quantity value in this range
RARE_QUANTITY_RANGE = (100, 1000)


# ----- Initial prices of store items -----

CAPACITY_INCREASE_COST = 250
PLANET_DESTRUCTION_COST = 100000
WAREHOUSE_SPEED_INCREASE_COST = 50000
PLANET_EXPLORATION_COST = 5000000
PLANET_EXPLORATION_UPGRADE_COST = 250000

# ----- Misc. values -----

# Planet exploration will initially yield some number of new planets in this range
PLANET_DISCOVERY_RANGE = (2, 8)

# Must be a power of 2
MAX_PLANET_DISCOVERY_RANGE_UPPER = 512

# Number of warehouse retrieval operations allowed per day
WAREHOUSE_GETS_PER_DAY = 1

# Number of warehouse storage operations allowed per day
WAREHOUSE_PUTS_PER_DAY = 1

# Amount to increase capacity by
CAPACITY_INCREASE = 100

# Max. length of names for high scores
MAX_HIGHSCORE_NAME_LEN = 32

# Quanity range required when giving a sample of a new item to a planet
ITEM_SAMPLE_QUANTITY_RANGE = (2, 10)

# Chance that giving a free sample will be successful, in percent
ITEM_SAMPLE_SUCCESS_PERCENT = 75

# If this number of planets or greater is currently loaded, disable planet discovery
# until some planets are destroyed
MAX_PLANETS_ALLOWED = 2000

# Max. times per day player can buy something from the store
MAX_STORE_PURCHASES_PER_DAY = 4

# Text shown in the intro dialog
GAME_INTRO_TEXT = (
    "The year is 81899, and you are the operator of an inter-planetary "
    "commercial trading vessel. You make your living by collecting various "
    "resources and treasures from countless planets across the galaxy, and "
    "selling them wherever you can.<br><br>"
    "Make as much money as you possibly can before your time runs out."
)

# Text shown in the Help->About dialog
GAME_ABOUT_TEXT = (
    ("Deep Space Trader %s<br><br>" % (package_version)) +
    ("Created by %s (%s)<br><br><br>" % (package_author, author_email)) +
    ("Deep Space Trader is written in python! Play it on any system that "
     "supports Python 3.<br><br>"
     "Install from Pypi:<br>"
     "&nbsp;&nbsp;pip install deep_space_trader<br><br>"
     "Run the installed package as a module:<br>"
     "&nbsp;&nbsp;python -m deep_space_trader")
)
