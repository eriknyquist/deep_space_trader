from PyQt5.QtCore import QT_TRANSLATE_NOOP


# ------ Initial values for player data on day 1 ------

INITIAL_MONEY = 2000000000
INITIAL_ITEM_CAPACITY = 100
INITIAL_PLANET_COUNT = 20000
INITIAL_MAX_DAYS = 30
INITIAL_SCOUT_LEVEL = 0
INITIAL_BATTLE_LEVEL = 0

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
TRADING_CONSOLE_COST = 3000

# ----- Daily costs -----

DAILY_LIVING_COST = 200
DAILY_TRADING_CONSOLE_COST = 500
DAILY_BATTLE_FLEET_COST_PER_LEVEL = 100000
DAILY_SCOUT_FLEET_COST_PER_LEVEL = 50000

# ----- Distances and travel -----

# Starting planets are placed up to this many light-years (ly) from the home planet.
# Scout expeditions find planets between this distance and
# (INITIAL_GALAXY_RADIUS * (scout level + 1)) ly from the home planet
INITIAL_GALAXY_RADIUS = 30.0

# Travel cost per light-year, before any engine upgrades
TRAVEL_COST_PER_LY = 5.0

# Smallest possible travel cost
MIN_TRAVEL_COST = 10

# Each engine power increase multiplies the travel cost per light-year by this
ENGINE_TRAVEL_COST_FACTOR = 0.75

# Max. number of times the engine power store item can be bought
MAX_ENGINE_LEVEL = 10

# Item prices on remote planets are lower, falling steadily from normal prices at
# INITIAL_GALAXY_RADIUS to this fraction of normal at the edge of the largest scout range
REMOTE_PRICE_FACTOR = 0.5

# The chance of meeting pirates is multiplied by (trip distance / PIRATE_REFERENCE_DISTANCE),
# kept within PIRATE_DISTANCE_FACTOR_RANGE, and capped at MAX_PIRATE_CHANCE_PERCENTAGE
PIRATE_REFERENCE_DISTANCE = 30.0
PIRATE_DISTANCE_FACTOR_RANGE = (0.5, 3.0)
MAX_PIRATE_CHANCE_PERCENTAGE = 95.0

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

# Initial number of warehouse trips allowed per day
WAREHOUSE_TRIPS_PER_DAY = 2

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

# Number of high scores stored
MAX_HIGH_SCORES = 10

# Language to use instead of the system language, e.g. "pt_BR" for Brazilian
# Portuguese, or None to use the system language. Also sets how numbers are
# formatted (e.g. 1.000.000 instead of 1,000,000)
#FORCE_LANGUAGE = "pt_BR"
FORCE_LANGUAGE = None

# Text shown in the intro dialog. Marked for translation here, and translated
# when shown (see utils.gameStoryDialog), since translations aren't loaded yet
# when this module is imported
GAME_INTRO_TEXT = QT_TRANSLATE_NOOP("About",
    "The year is 5208, and humanity has solved the problem of bridging the vast "
    "distances between stars by bending the fabric of spacetime. Commerce between "
    "thousands of newly colonized planets is now possible.<br><br>"
    "You are the owner of an inter-planetary commercial trading vessel. You make "
    "your living by purchasing and harvesting raw materials and resources from "
    "countless planets across the universe, and selling them to other planets.<br><br>"
    "If you encounter pirates and do not have sufficient weaponry to defend yourself, "
    "you will be robbed, or you will die.<br><br>"
    "If you don't make enough money to keep up with your daily costs, you will die.<br><br>"
    "Your daily costs will increase as you purchase services that require daily "
    "maintenance.<br><br>"
    "Don't die, and make as much money as you possibly can before your time runs out."
)

# Text shown in the "game complete" dialog
GAME_COMPLETE_TEXT = (
    ""
)

# Strategy tips shown in the Help->About dialog, after the intro text (see
# utils.showAboutDialog). Translated when shown, like GAME_INTRO_TEXT
GAME_ABOUT_STRATEGY_TEXT = QT_TRANSLATE_NOOP("About",
    "<ul>Recommended strategy: <br>"
    "<li>Buy the 'Increase ship capacity' upgrade from the store as early and as "
    "frequently as possible</li><br>"
    "<li>Destroy as many planets as you can, by buying the 'Planet destruction "
    "kit' from the store</li><br>"
    "<li>Discover new planets by buying 'Scout expedition' from "
    "the store, and sell them the resources you obtained from destroying "
    "other planets. Rinse and repeat.</li><br>"
    "<li>Watch out for pirates and planets that resist destruction; buy the "
    "Battle Fleet from the store and upgrade it as often as you can to increase "
    "your chances of winning battles against pirate fleets and planet defense fleets.</li></ul>"
)
