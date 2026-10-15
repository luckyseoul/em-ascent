import math

import pytest

from em_ascent.constants import G0, G_MOON
from em_ascent.lunar import (
    electrical_j_per_kg,
    hop_range,
    landing_mass_fraction,
    speed_for_range,
    supplies_kg,
    thrown_for_bank_j,
    tube_length,
)


def test_forty_five_degree_hop_is_v_squared_over_g():
    v = 110.0
    assert hop_range(v, 45.0) == pytest.approx(v * v / G_MOON)


def test_range_and_speed_are_inverses():
    v = speed_for_range(20_000.0, 45.0)
    assert hop_range(v, 45.0) == pytest.approx(20_000.0, rel=1e-12)


def test_landing_burn_matches_the_rocket_equation():
    dv = 130.0
    isp = 220.0
    assert landing_mass_fraction(dv, isp) == pytest.approx(math.exp(-dv / (isp * G0)))


def test_small_package_pays_the_inert_floor():
    assert supplies_kg(1.5) < supplies_kg(1.5, catch=True)
    assert supplies_kg(1.0) > 0.0


def test_bank_energy_scales_the_thrown_mass():
    per_kg = electrical_j_per_kg(110.0, 14.0, 45.0)
    assert thrown_for_bank_j(per_kg * 10.0, 110.0, 14.0, 45.0) == pytest.approx(10.0)
    assert tube_length(110.0, 14.0) == pytest.approx(110.0**2 / (2.0 * 14.0 * G0))
