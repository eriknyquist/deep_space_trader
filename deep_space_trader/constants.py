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
COMMON_QUANTITY_RANGE = (1000, 1000000)

# Generated medium rare items will always have a quantity value in this range
MEDIUM_RARE_QUANTITY_RANGE = (1000, 100000)

# Generated rare items will always have a quantity value in this range
RARE_QUANTITY_RANGE = (100, 10000)


# ----- Initial prices of store items -----

CAPACITY_INCREASE_COST = 250
PLANET_DESTRUCTION_COST = 2000000
WAREHOUSE_SPEED_INCREASE_COST = 50000
PLANET_EXPLORATION_COST = 50000000
PLANET_EXPLORATION_UPGRADE_COST = 750000
BATTLE_UPGRADE_COST = 250000

# ----- Misc. values -----

# Percentage chance of getting a random trading tip about a price anomaly, each day
CHANCE_TRADING_TIP_PERCENTAGE = 15.0

# Percentage chance of a received trading tip being accurate
TRADING_TIP_ACCURACY_PERCENTAGE = 70.0

# Max. number of times the battle fleet upgrade store item can be bought
MAX_BATTLE_LEVEL = 10

# Max. number of times the scout fleet upgrade store item can be bought
MAX_SCOUT_LEVEL = 10

# Planet exploration will initially yield some number of new planets in this range
PLANET_DISCOVERY_RANGE = (4, 8)

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
MAX_PLANETS_ALLOWED = 20000

# Max. times per day player can buy something from the store
MAX_STORE_PURCHASES_PER_DAY = 4

# Text shown in the intro dialog
GAME_INTRO_TEXT = (
    "The year is 81899, and you are the owner of an inter-planetary commercial "
    "trading vessel. You make your living by purchasing and harvesting "
    "raw materials and resources from countless planets across the galaxy, and "
    "selling them wherever you can.<br><br>"
    "Make as much money as you possibly can before your time runs out."
)

# Text shown in the "game complete" dialog
GAME_COMPLETE_TEXT = (
    ""
)

# Text shown in the Help->About dialog
GAME_ABOUT_TEXT = (
    ("Deep Space Trader %s<br><br>" % (package_version)) +
    ("Created by %s (%s)<br><br>" % (package_author, author_email)) +
    ("<ul>Recommended strategy: <br>" +
     "<li>Buy the 'Increase item capacity' upgrade from the store as early and as " +
     " frequently as possible</li><br>" +
     "<li>Destroy as many planets as you can, by buying the 'Planet destruction " +
     "kit' from the store</li><br>" +
     "<li>Discover new planets by buying 'Scout expedition' from " +
     "the store, and sell them the resources you obtained from destroying " +
     " other planets. Rinse and repeat.</li><br>" +
     "<li>Watch out for pirates and planets that resist destruction; buy the " +
     "Battle Fleet from the store and upgrade it as often as you can to increase " +
     "your chances of winning battles against pirate fleets and planet defense fleets.</li></ul><br><br>" +
     "Deep Space Trader is written in python! Play it on any system that " +
     "supports Python 3.<br><br>" +
     "Install from Pypi:<br>" +
     "&nbsp;&nbsp;pip install deep_space_trader<br><br>" +
     "Run the installed package as a module:<br>" +
     "&nbsp;&nbsp;python -m deep_space_trader")
)
