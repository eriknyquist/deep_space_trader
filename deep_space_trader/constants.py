from PyQt5.QtCore import QT_TRANSLATE_NOOP


# ------ Initial values for player data on day 1 ------

INITIAL_MONEY = 2000
INITIAL_ITEM_CAPACITY = 100
INITIAL_PLANET_COUNT = 8
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

# Contraband (only traded on black markets)
PRICE_TOBACCO = 250
PRICE_LIQUOR = 300
PRICE_STIMULANTS = 400
PRICE_CREDIT_CHIPS = 600
PRICE_AMMUNITION = 800


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

# Planets are grouped in clusters rather than spread evenly. This fraction of new
# planets is placed near a cluster centre, and the rest anywhere in their area
CLUSTER_FRACTION = 0.7

# Average number of new planets per new cluster
CLUSTER_SIZE = 8

# How far planets in a cluster are scattered around its centre (standard deviation, in ly)
CLUSTER_SPREAD_LY = 4.0

# Planets with the same name and number, but different letters (e.g. "Kandar 12 c"
# and "Kandar 12 d"), are in the same star system: scattered this closely (in ly)
STAR_SYSTEM_SPREAD_LY = 1.0

# Item prices on remote planets are lower, falling steadily from normal prices at
# INITIAL_GALAXY_RADIUS to this fraction of normal at the edge of the largest scout range
REMOTE_PRICE_FACTOR = 0.5

# The chance of meeting pirates is multiplied by (trip distance / PIRATE_REFERENCE_DISTANCE),
# kept within PIRATE_DISTANCE_FACTOR_RANGE, and capped at MAX_PIRATE_CHANCE_PERCENTAGE
PIRATE_REFERENCE_DISTANCE = 30.0
PIRATE_DISTANCE_FACTOR_RANGE = (0.5, 3.0)
MAX_PIRATE_CHANCE_PERCENTAGE = 95.0

# ----- Reputation -----

# Every planet's opinion of the player starts here (reputation goes from 0 to 100)
STARTING_REPUTATION = 70

# Below this reputation, a planet won't trade with the player
REFUSE_TRADE_REPUTATION = 15

# Reputation at the start of each level: Allied, Friendly, Wary, Hostile (below
# REFUSE_TRADE_REPUTATION, a planet refuses to trade)
ALLIED_REPUTATION = 85
FRIENDLY_REPUTATION = 70
WARY_REPUTATION = 45

# Reputation changes at the place where something happens
DESTRUCTION_REPUTATION = -15         # per destroyed planet
RESISTANCE_FIGHT_REPUTATION = -10    # fighting a planet that resists destruction, win or lose
SALE_REPUTATION = 2                  # selling to a planet (counts once per planet per day)
SAMPLE_REPUTATION = 3                # a planet accepts a free sample

# How far news spreads: a change is half as strong this many light-years away
DESTRUCTION_SPREAD_LY = 40.0
TRADE_SPREAD_LY = 15.0

# Every reputation change is multiplied by this each day, so it fades away
DAILY_REPUTATION_RECOVERY = 0.93

# At reputation 0, buy prices are (1 + WORST_PRICE_FACTOR) times normal and sell
# prices (1 - WORST_PRICE_FACTOR); at reputation 100, buy prices are
# (1 - BEST_PRICE_FACTOR) times normal and sell prices (1 + BEST_PRICE_FACTOR)
WORST_PRICE_FACTOR = 0.5
BEST_PRICE_FACTOR = 0.1

# Size of the cells reputation is stored in, in light-years
REPUTATION_GRID_LY = 5.0

# ----- Contraband -----

# Percentage of planets that are black markets (the same everywhere; never the home planet)
BLACK_MARKET_CHANCE_PERCENTAGE = 12.5

# How many of the contraband types each black market stocks, and how many of each
BLACK_MARKET_TYPES_RANGE = (2, 4)
BLACK_MARKET_QUANTITY_RANGE = (50, 2000)

# Each black market's price for each contraband type, as a multiple of its base price
BLACK_MARKET_PRICE_FACTOR_RANGE = (0.3, 3.0)

# Chance of a customs inspection on a trip with contraband on the ship:
# INSPECTION_CHANCE_PERCENTAGE, plus INSPECTION_CHANCE_PER_100_UNITS for every 100
# units carried, multiplied by 1 (reputation Friendly or better) up to 2
# (reputation 0) at the destination, and capped at MAX_INSPECTION_CHANCE_PERCENTAGE
INSPECTION_CHANCE_PERCENTAGE = 10.0
INSPECTION_CHANCE_PER_100_UNITS = 2.0
MAX_INSPECTION_CHANCE_PERCENTAGE = 60.0

# A search that finds contraband seizes it, with a fine of this times its value
CONTRABAND_FINE_FRACTION = 1.0

# A bribe costs this times the contraband's value. It works BRIBE_SUCCESS_PERCENTAGE
# of the time at STARTING_REPUTATION, plus or minus BRIBE_SUCCESS_PER_REPUTATION
# for each point of reputation above or below that (so from 35% to 85%)
BRIBE_COST_FRACTION = 0.3
BRIBE_SUCCESS_PERCENTAGE = 70.0
BRIBE_SUCCESS_PER_REPUTATION = 0.5

# Chance of escaping a customs patrol by fleeing, plus this for each engine power level
FLEE_ESCAPE_PERCENTAGE = 30.0
FLEE_ESCAPE_PER_ENGINE_LEVEL = 6.0
MAX_FLEE_ESCAPE_PERCENTAGE = 90.0

# Hidden cargo hold store upgrade: price of each level, and the chance at each
# level that a search finds nothing
HIDDEN_HOLD_COSTS = (100000, 500000, 2000000)
HIDDEN_HOLD_NOTHING_FOUND_PERCENTAGES = (25.0, 45.0, 60.0)

# Reputation changes at the destination of the trip
FAILED_BRIBE_REPUTATION = -10        # the officers took the bribe, then searched anyway
ESCAPED_PATROL_REPUTATION = -10      # fled, and got away ("wanted")
CAUGHT_FLEEING_REPUTATION = -15      # fled, and got caught (spreads like destruction news)
CONTRABAND_FOUND_REPUTATION = -5     # let them search, and they found contraband

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
    "<li>The 'Planet destruction kit' from the store gets you all of a planet's "
    "resources at once, but planets remember: the planets around it will charge "
    "you more, pay you less, and may even refuse to trade with you. Choose your "
    "targets carefully, and don't destroy too many planets in one area.</li><br>"
    "<li>Sell the resources from destroyed planets far from where you destroyed "
    "them, for example on new planets found with 'Scout expedition' from the "
    "store. Trading with planets slowly wins them back over.</li><br>"
    "<li>Watch out for pirates and planets that resist destruction; buy the "
    "Battle Fleet from the store and upgrade it as often as you can to increase "
    "your chances of winning battles against pirate fleets and planet defense fleets.</li><br>"
    "<li>Contraband sells for far more than legal goods, but only black markets trade it, "
    "and you only find black markets by visiting them. Carry small loads: the more "
    "contraband on your ship, the more likely a customs patrol is to stop you.</li></ul>"
)
