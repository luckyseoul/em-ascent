import math

import pytest

from em_ascent.ascent import Vehicle, simulate_ascent
from em_ascent.constants import G0


def test_drag_free_vertical_toss():
    vehicle = Vehicle(1.0, 0.0, 200.0, 0.07, 0.0, 0.0)
    flown = simulate_ascent(vehicle, 0.0, 10.0, 0.0, 100.0, math.pi / 2)
    assert flown.apogee_m == pytest.approx(10.0 + 100.0**2 / (2.0 * G0), rel=1e-3)


def test_gentle_motor_climbs_from_the_muzzle():
    vehicle = Vehicle(1.10, 0.40, 205.0, 0.070, 0.50, 3.5 * 1.50 * G0)
    gamma = math.radians(65.0)
    speed = 110.0
    flown = simulate_ascent(
        vehicle,
        8.0,
        20.0,
        speed * math.cos(gamma),
        speed * math.sin(gamma),
        gamma,
        clearance_m=0.45,
    )
    assert flown.apogee_m > 20.0
    assert flown.t_gate_s is not None
    assert flown.t_gate_s < 2.0


def test_rail_keeps_the_launch_angle():
    gamma = math.radians(65.0)
    vehicle = Vehicle(1.10, 0.40, 205.0, 0.070, 0.50, 14.0 * 1.50 * G0)
    flown = simulate_ascent(
        vehicle,
        0.0,
        0.3,
        0.4 * math.cos(gamma),
        0.4 * math.sin(gamma),
        gamma,
        rail_m=2.0,
    )
    # First free-flight sample is past the rail. Heading should still be the rail angle.
    # x and h arrays include the rail, so use a point near 2 m of slant range.
    slant = (flown.x**2 + (flown.h - 0.3) ** 2) ** 0.5
    i = int((abs(slant - 2.0)).argmin())
    # Reconstruct heading from neighboring samples once the rail has been left.
    j = min(i + 3, len(flown.x) - 1)
    heading = math.atan2(flown.h[j] - flown.h[i], flown.x[j] - flown.x[i])
    assert heading == pytest.approx(gamma, abs=0.08)
