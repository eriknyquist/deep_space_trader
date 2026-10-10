import time
import random

import pytest

from deep_space_trader import constants as const
from deep_space_trader import reputation as rep
from deep_space_trader.reputation import Reputation


def value(r, x, y):
    return float(r.at([x], [y])[0])


def test_starts_at_starting_reputation():
    r = Reputation()
    for x, y in ((0, 0), (100, -50), (-300, 300)):
        assert value(r, x, y) == const.STARTING_REPUTATION


def test_event_is_strongest_where_it_happens():
    r = Reputation()
    r.addEvent(100, 50, -20, 40)
    centre = value(r, 100, 50)
    assert centre == pytest.approx(const.STARTING_REPUTATION - 20, abs=1.5)
    # About half as strong at 'spread' ly away, and nearly nothing far away
    assert value(r, 140, 50) - const.STARTING_REPUTATION == pytest.approx(-10, abs=1.5)
    assert value(r, 200, 50) - const.STARTING_REPUTATION == pytest.approx(0, abs=0.5)
    assert value(r, -200, -200) == const.STARTING_REPUTATION


def test_events_add_up():
    r = Reputation()
    r.addEvents([(0, 0), (0, 0), (2, 1)], -10, 40)
    assert value(r, 0, 0) == pytest.approx(const.STARTING_REPUTATION - 30, abs=2)


def test_good_events_raise_reputation():
    r = Reputation()
    r.addEvent(-50, 20, 5, 15)
    assert value(r, -50, 20) == pytest.approx(const.STARTING_REPUTATION + 5, abs=0.5)


def test_reputation_stays_between_0_and_100():
    r = Reputation()
    r.addEvents([(0, 0)] * 20, -15, 40)
    assert value(r, 0, 0) == 0.0
    r = Reputation()
    r.addEvents([(0, 0)] * 20, 15, 15)
    assert value(r, 0, 0) == 100.0


def test_changes_fade_each_day():
    r = Reputation()
    r.addEvent(0, 0, -20, 40)
    before = value(r, 0, 0) - const.STARTING_REPUTATION
    r.nextDay()
    after = value(r, 0, 0) - const.STARTING_REPUTATION
    assert after == pytest.approx(before * const.DAILY_REPUTATION_RECOVERY)

    for _ in range(100):
        r.nextDay()
    assert value(r, 0, 0) == pytest.approx(const.STARTING_REPUTATION, abs=0.05)


def test_events_at_the_edge_of_the_galaxy():
    furthest = const.INITIAL_GALAXY_RADIUS * (const.MAX_SCOUT_LEVEL + 1)
    r = Reputation()
    r.addEvent(furthest, 0, -20, 40)
    assert value(r, furthest, 0) == pytest.approx(const.STARTING_REPUTATION - 20, abs=1.5)
    # Positions beyond the grid don't break anything
    assert 0 <= value(r, 10000, 10000) <= 100


def test_levels():
    assert rep.level(100) == rep.ALLIED
    assert rep.level(const.ALLIED_REPUTATION) == rep.ALLIED
    assert rep.level(const.STARTING_REPUTATION) == rep.FRIENDLY
    assert rep.level(const.WARY_REPUTATION) == rep.WARY
    assert rep.level(const.REFUSE_TRADE_REPUTATION) == rep.HOSTILE
    assert rep.level(const.REFUSE_TRADE_REPUTATION - 0.4) == rep.HOSTILE
    assert rep.level(const.REFUSE_TRADE_REPUTATION - 0.6) == rep.REFUSES
    # Tiny changes left far from an event don't change the level
    assert rep.level(const.STARTING_REPUTATION - 1e-6) == rep.FRIENDLY
    assert rep.level(0) == rep.REFUSES


@pytest.mark.parametrize("reputation, buy, sell", [
    (const.STARTING_REPUTATION, 1.0, 1.0),
    (0, 1.0 + const.WORST_PRICE_FACTOR, 1.0 - const.WORST_PRICE_FACTOR),
    (100, 1.0 - const.BEST_PRICE_FACTOR, 1.0 + const.BEST_PRICE_FACTOR),
])
def test_price_factors(reputation, buy, sell):
    assert rep.buyPriceFactor(reputation) == pytest.approx(buy)
    assert rep.sellPriceFactor(reputation) == pytest.approx(sell)


def test_fast_with_many_planets_and_events():
    random.seed(1)
    r = Reputation()
    positions = [(random.uniform(-330, 330), random.uniform(-330, 330)) for _ in range(20000)]

    start = time.time()
    r.addEvents(positions, const.DESTRUCTION_REPUTATION, const.DESTRUCTION_SPREAD_LY)
    xs, ys = zip(*positions)
    values = r.at(xs, ys)
    assert len(values) == 20000
    assert time.time() - start < 2
