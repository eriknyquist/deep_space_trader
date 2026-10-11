"""
What happens when a customs patrol stops the player's ship (see
LocationBrowser.travelToPlanet). Each choice the player can make is a plain
function that changes the game state and returns an Outcome, so that the
window only has to show it
"""
from deep_space_trader import constants as const
from deep_space_trader.utils import percentChance


class Outcome(object):
    def __init__(self):
        self.bribe_paid = 0         # money paid in a bribe
        self.bribed = False         # the bribe worked
        self.bribe_failed = False   # the bribe didn't work
        self.escaped = False        # fled, and got away
        self.caught = False         # fled, and got caught
        self.searched = False       # the patrol searched the ship
        self.found = False          # ... and found the contraband
        self.seized_value = 0       # value of the seized contraband
        self.fine = 0               # fine paid


def search(state, planet, outcome):
    """
    The patrol searches the ship. With a hidden cargo hold, they may find
    nothing; otherwise they seize all contraband on the ship, and fine the
    player (up to all their money)
    """
    outcome.searched = True
    if percentChance(state.hidden_hold_chance()):
        return outcome

    outcome.found = True
    outcome.seized_value = state.contraband_value(planet)
    outcome.fine = state.contraband_fine(planet)
    state.money -= outcome.fine

    for item in state.contraband_on_ship():
        state.items.remove_items(item.type.name, item.quantity)

    return outcome


def let_them_search(state, planet):
    outcome = search(state, planet, Outcome())
    if outcome.found:
        state.customs_event(planet, const.CONTRABAND_FOUND_REPUTATION)

    return outcome


# Choices offered to the player when a patrol stops them, in the order of
# the buttons (see LocationBrowser.customsInspection)
BRIBE, FLEE, LET_THEM_SEARCH = range(3)


def bribe(state, planet):
    """
    Pay the patrol to look the other way. If it doesn't work, they keep the
    money and search the ship anyway
    """
    outcome = Outcome()
    outcome.bribe_paid = min(state.money, state.bribe_cost(planet))
    success_chance = state.bribe_success_chance(planet)
    state.money -= outcome.bribe_paid

    if percentChance(success_chance):
        outcome.bribed = True
        return outcome

    outcome.bribe_failed = True
    state.customs_event(planet, const.FAILED_BRIBE_REPUTATION)
    return search(state, planet, outcome)


def flee(state, planet):
    """
    Try to outrun the patrol. If they catch the ship, it's damaged in the
    chase (as in a lost battle), and searched
    """
    outcome = Outcome()
    if percentChance(state.flee_escape_chance()):
        outcome.escaped = True
        state.customs_event(planet, const.ESCAPED_PATROL_REPUTATION)
        return outcome

    outcome.caught = True
    state.lost_health_from_battle()
    state.disable_health_recovery_today()
    state.customs_event(planet, const.CAUGHT_FLEEING_REPUTATION, const.DESTRUCTION_SPREAD_LY)
    return search(state, planet, outcome)
