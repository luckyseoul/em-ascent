import math

import pytest

from em_ascent.path import gamma_kappa, make_turn, peak_normal_over_axial


def test_turn_leaves_at_the_launch_angle():
    turn = make_turn(8.0, 65.0, 3.0, 0.30)
    gamma0, kappa0 = gamma_kappa(0.0, turn)
    gamma1, kappa1 = gamma_kappa(turn.s_turn_m, turn)
    assert gamma0 == pytest.approx(turn.gamma0_rad)
    assert kappa0 == 0.0
    assert gamma1 == pytest.approx(turn.gamma1_rad)
    assert kappa1 == 0.0


def test_curvature_peaks_at_one_over_radius():
    turn = make_turn(8.0, 70.0, 2.5, 0.30)
    samples = [i * turn.s_turn_m / 200.0 for i in range(201)]
    kappas = [gamma_kappa(s, turn)[1] for s in samples]
    assert max(kappas) == pytest.approx(1.0 / 2.5, rel=1e-6)
    assert kappas[0] == 0.0
    assert kappas[-1] == 0.0


def test_constant_accel_normal_ratio():
    delta = math.radians(50.0)
    assert peak_normal_over_axial(delta) == pytest.approx(2.0 * delta)
