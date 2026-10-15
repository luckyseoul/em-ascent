import pytest

from em_ascent.constants import G0
from em_ascent.tube import TubeSpec, mechanical_energy_balance, simulate_tube, straight_length


def _spec(**overrides) -> TubeSpec:
    base = dict(
        mass_kg=1.5,
        v_exit=110.0,
        a_turn=6.0 * G0,
        a_barrel=18.0 * G0,
        gamma0_deg=8.0,
        gamma1_deg=65.0,
        radius_m=3.0,
        eta_coil=0.20,
    )
    base.update(overrides)
    return TubeSpec(**base)


def test_straight_length_formula():
    assert straight_length(100.0, 20.0) == pytest.approx(250.0)


def test_shot_hits_exit_speed_and_conserves_work():
    shot = simulate_tube(_spec())
    assert shot.feasible
    assert shot.v[-1] == pytest.approx(110.0, rel=0.02)
    assert shot.h[-1] > 5.0
    balance = mechanical_energy_balance(shot)
    assert balance["work_j"] == pytest.approx(balance["ke_pe_fric_j"], rel=0.03)
    assert balance["electrical_j"] == pytest.approx(balance["work_j"] / 0.20, rel=0.02)


def test_fast_turn_can_finish_the_shot_inside_the_curve():
    shot = simulate_tube(
        _spec(v_exit=25.0, a_turn=50.0 * G0, a_barrel=50.0 * G0, radius_m=6.0, gamma1_deg=75.0)
    )
    assert shot.exited_in_turn
    assert not shot.feasible
