import math

import pytest

from em_ascent.bearings import (
    HARD_RACE_E_PA,
    HARD_RACE_NU,
    SI3N4_E_PA,
    SI3N4_NU,
    chordal_rise,
    hertz_sphere_on_flat,
    reduced_modulus,
)


def test_hertz_matches_closed_form():
    estar = reduced_modulus(SI3N4_E_PA, SI3N4_NU, HARD_RACE_E_PA, HARD_RACE_NU)
    force = 40.0
    radius = 0.004
    contact, pmax = hertz_sphere_on_flat(force, radius, estar)
    expected = (1.0 / math.pi) * (6.0 * force * estar**2 / radius**2) ** (1.0 / 3.0)
    assert pmax == pytest.approx(expected, rel=1e-12)
    assert contact > 0.0


def test_pressure_scales_with_force_to_the_one_third():
    estar = reduced_modulus(SI3N4_E_PA, SI3N4_NU, HARD_RACE_E_PA, HARD_RACE_NU)
    _, p1 = hertz_sphere_on_flat(20.0, 0.004, estar)
    _, p8 = hertz_sphere_on_flat(160.0, 0.004, estar)
    assert p8 / p1 == pytest.approx(2.0, rel=1e-12)


def test_zero_force_is_no_contact():
    assert hertz_sphere_on_flat(0.0, 0.004, 1e11) == (0.0, 0.0)


def test_short_pad_clears_a_tight_breech_turn():
    rise = chordal_rise(1.5, 0.025)
    assert rise == pytest.approx(0.025**2 / (8.0 * 1.5))
    assert rise < 0.0002
