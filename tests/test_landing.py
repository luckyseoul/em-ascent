import math

import pytest

from em_ascent.constants import G0
from em_ascent.landing import catch_stroke, chute_terminal_mps, numpy_one


def test_catch_stroke_is_the_kinematic_stop():
    assert catch_stroke(110.0, 15.0) == pytest.approx(110.0**2 / (2.0 * 15.0 * G0))


def test_chute_terminal_speed():
    mass = 1.5
    diameter = 0.9
    cd = 1.5
    rho = 1.225
    area = math.pi * 0.25 * diameter**2
    expect = math.sqrt(2.0 * mass * G0 / (rho * cd * area))
    assert chute_terminal_mps(mass, diameter, cd, rho) == pytest.approx(expect)
    assert expect < 8.0


def test_no_wind_ballistic_leaves_the_pad_downrange():
    flown = numpy_one(110.0, 65.0, 20.6, 42.3, chute_diameter_m=None)
    assert flown["apogee_m"] > 42.3
    assert flown["range_m"] > 100.0
    assert flown["speed"] > 20.0
