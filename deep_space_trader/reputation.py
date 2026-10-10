"""
How much planets like the player. Each planet's reputation depends on what the
player has done nearby: events (destroying planets, trading, ...) change
reputation most where they happen, and less further away. Every change fades
a little each day.

There can be 20,000 planets, and thousands of events at once (e.g. "Destroy
all"), so reputation is stored as a grid of reputation changes covering the
galaxy, rather than as a list of events that every planet adds up.
"""
import math

import numpy
from PyQt5.QtCore import QT_TRANSLATE_NOOP

from deep_space_trader import constants as const
from deep_space_trader.i18n import translate, formatNumber


def gridRadius():
    """
    Distance from home that the grid covers: the furthest possible planet, plus
    room for the news of an event there to spread
    """
    furthest_planet = const.INITIAL_GALAXY_RADIUS * (const.MAX_SCOUT_LEVEL + 1)
    return furthest_planet + 3 * max(const.DESTRUCTION_SPREAD_LY, const.TRADE_SPREAD_LY)


def spreadKernel(spread):
    """
    1D falloff for an event: 1.0 at the centre, 0.5 at 'spread' ly, nearly 0
    at 3 * 'spread' ly. Because exp(-a(x^2 + y^2)) = exp(-ax^2) * exp(-ay^2),
    using it along rows and then along columns gives the 2D falloff
    """
    cells = int(math.ceil(3 * spread / const.REPUTATION_GRID_LY))
    distances = numpy.arange(-cells, cells + 1) * const.REPUTATION_GRID_LY
    return numpy.exp(-math.log(2) * (distances / spread) ** 2)


class Reputation(object):
    def __init__(self):
        self.radius = gridRadius()
        self.size = int(math.ceil(2 * self.radius / const.REPUTATION_GRID_LY)) + 1

        # Change from STARTING_REPUTATION at each cell's centre; [row, column] = [y, x]
        self.grid = numpy.zeros((self.size, self.size))

        # Goes up whenever any reputation changes, so displays can skip
        # refreshing thousands of planets when nothing has changed
        self.version = 0

    def cellIndex(self, values):
        """
        Grid index of the cells nearest to positions (in ly)
        """
        return numpy.rint((numpy.asarray(values, dtype=float) + self.radius) / const.REPUTATION_GRID_LY).astype(int)

    def addEvents(self, positions, amount, spread):
        """
        Change reputation by 'amount' (positive or negative) at each (x, y)
        position, spreading out as set by 'spread'
        """
        if not positions:
            return

        xs, ys = zip(*positions)
        columns = numpy.clip(self.cellIndex(xs), 0, self.size - 1)
        rows = numpy.clip(self.cellIndex(ys), 0, self.size - 1)

        # Mark each event's cell, then blur the marks into smooth bumps
        marks = numpy.zeros_like(self.grid)
        numpy.add.at(marks, (rows, columns), amount)

        kernel = spreadKernel(spread)
        marks = numpy.apply_along_axis(lambda row: numpy.convolve(row, kernel, mode="same"), 1, marks)
        marks = numpy.apply_along_axis(lambda column: numpy.convolve(column, kernel, mode="same"), 0, marks)
        self.grid += marks
        self.version += 1

    def addEvent(self, x, y, amount, spread):
        self.addEvents([(x, y)], amount, spread)

    def nextDay(self):
        """
        Every change fades a little each day
        """
        if self.grid.any():
            self.grid *= const.DAILY_REPUTATION_RECOVERY
            self.version += 1

    def at(self, xs, ys):
        """
        Reputation (0-100) at each position, blended between the nearest cells
        """
        xs = (numpy.asarray(xs, dtype=float) + self.radius) / const.REPUTATION_GRID_LY
        ys = (numpy.asarray(ys, dtype=float) + self.radius) / const.REPUTATION_GRID_LY
        x0 = numpy.clip(numpy.floor(xs).astype(int), 0, self.size - 2)
        y0 = numpy.clip(numpy.floor(ys).astype(int), 0, self.size - 2)
        fx = numpy.clip(xs - x0, 0.0, 1.0)
        fy = numpy.clip(ys - y0, 0.0, 1.0)

        g = self.grid
        change = (g[y0, x0] * (1 - fx) * (1 - fy) + g[y0, x0 + 1] * fx * (1 - fy) +
                  g[y0 + 1, x0] * (1 - fx) * fy + g[y0 + 1, x0 + 1] * fx * fy)
        return numpy.clip(const.STARTING_REPUTATION + change, 0.0, 100.0)

    def ofPlanet(self, planet):
        return float(self.at([planet.x], [planet.y])[0])

    def ofPlanets(self, planets):
        """
        Reputation of many planets at once (much faster than one at a time)
        """
        return self.at([p.x for p in planets], [p.y for p in planets])


# Reputation levels, from best to worst
ALLIED = 0
FRIENDLY = 1
WARY = 2
HOSTILE = 3
REFUSES = 4


# Translated when used, since translations aren't loaded yet when this module is imported
LEVEL_NAMES = [
    QT_TRANSLATE_NOOP("Reputation", "Allied"),
    QT_TRANSLATE_NOOP("Reputation", "Friendly"),
    QT_TRANSLATE_NOOP("Reputation", "Wary"),
    QT_TRANSLATE_NOOP("Reputation", "Hostile"),
    QT_TRANSLATE_NOOP("Reputation", "Refuses to trade"),
]

# Traffic light colours for each level, used by the info bar and the star map
LEVEL_COLORS = ["#00c853", "#9ccc3c", "#ffd600", "#ff8f00", "#e53935"]

# Colours of the messages about better or worse prices (in the Buy and Sell
# windows, and for "Sell all"). Readable with both the light and dark themes
GOOD_PRICE_COLOR = "#2ea043"
BAD_PRICE_COLOR = "#e53935"


def shownNumber(reputation):
    """
    Reputation as the whole number the player sees. Levels (and refusal to
    trade) go by this number, so they always match it, and so that the tiny
    changes left far from an event don't turn a planet at 69.999 Wary
    """
    return int(math.floor(reputation + 0.5))


def level(reputation):
    reputation = shownNumber(reputation)
    if reputation >= const.ALLIED_REPUTATION:
        return ALLIED
    if reputation >= const.FRIENDLY_REPUTATION:
        return FRIENDLY
    if reputation >= const.WARY_REPUTATION:
        return WARY
    if reputation >= const.REFUSE_TRADE_REPUTATION:
        return HOSTILE
    return REFUSES


def buyPriceFactor(reputation):
    """
    Multiply a planet's price by this when the player buys from it
    """
    start = const.STARTING_REPUTATION
    if reputation < start:
        return 1.0 + const.WORST_PRICE_FACTOR * (start - reputation) / start

    return 1.0 - const.BEST_PRICE_FACTOR * (reputation - start) / (100.0 - start)


def sellPriceFactor(reputation):
    """
    Multiply a planet's price by this when the player sells to it
    """
    start = const.STARTING_REPUTATION
    if reputation < start:
        return 1.0 - const.WORST_PRICE_FACTOR * (start - reputation) / start

    return 1.0 + const.BEST_PRICE_FACTOR * (reputation - start) / (100.0 - start)


def levelName(reputation):
    return translate("Reputation", LEVEL_NAMES[level(reputation)])


def levelColor(reputation):
    return LEVEL_COLORS[level(reputation)]


def describe(reputation):
    """
    Reputation as text, e.g. "Wary (58)"
    """
    return translate("Reputation", "{0} ({1})",
                     "{0} is a reputation level, e.g. Wary, and {1} is a number from 0 to 100").format(
                     levelName(reputation), formatNumber(shownNumber(reputation)))
