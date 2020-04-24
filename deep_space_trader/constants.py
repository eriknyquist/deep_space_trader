# ------ Initial values for player data on day 1 ------
INITIAL_MONEY = 1000
INITIAL_TRAVEL_COST = 100
INITIAL_ITEM_CAPACITY = 100
INITIAL_PLANET_COUNT = 12
INITIAL_MAX_DAYS = 30

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
COMMON_QUANTITY_RANGE = (100, 1000)

# Generated medium rare items will always have a quantity value in this range
MEDIUM_RARE_QUANTITY_RANGE = (100, 500)

# Generated rare items will always have a quantity value in this range
RARE_QUANTITY_RANGE = (10, 100)


# ----- Prices of store items -----

CAPACITY_INCREASE_COST = 250
PLANET_EXPLORATION_COST = 1000
PLANET_DESTRUCTION_COST = 2000

# ----- Misc. values -----

# Planet exploration will always yield some number of new planets in this range
PLANET_DISCOVERY_RANGE = (2, 12)

# Number of warehouse retrieval operations allowed per day
WAREHOUSE_GETS_PER_DAY = 1

# Number of warehouse storage operations allowed per day
WAREHOUSE_PUTS_PER_DAY = 1

# Amount to increase capacity by
CAPACITY_INCREASE = 100

# Max. length of names for high scores
MAX_HIGHSCORE_NAME_LEN = 32

# Text shown in the intro dialog
GAME_INTRO_TEXT = (
    "The year is 81899, and you are the operator of an inter-planetary "
    "commercial trading vessel. You make your living by collecting various "
    "resources and treasures from countless planets across the galaxy, and "
    "selling them wherever you can.<br><br>"
    "Make as much money as you possibly can before your time runs out."
)
