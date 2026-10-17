from em_ascent.constants import G0
from em_ascent.starship_assist import GLOW_KG, THRUST_SL_N, simulate


def test_liftoff_acceleration_matches_thrust_and_weight():
    flown = simulate(0.0, 0.0, 0.0, gate_m=20.0)
    # First meters are almost constant accel: v^2 = 2 a h
    a = THRUST_SL_N / GLOW_KG - G0
    expect = (2.0 * a * 20.0) ** 0.5
    assert flown["speed_mps"] == pytest_approx(expect, rel=0.03)


def test_reference_ring_leaves_about_fifteen_tonnes():
    from em_ascent.starship_assist import propellant_to_match

    row = propellant_to_match(5.0e6, 40.0)
    assert row["matched"]
    assert row["prop_offload_kg"] == pytest_approx(14_910.0, rel=0.08)
    assert row["speed_mps"] == pytest_approx(row["baseline_speed_mps"], abs=0.5)


def test_pusher_is_faster_at_the_gate():
    plain = simulate(0.0, 0.0, 0.0, gate_m=200.0)
    pushed = simulate(5.0e6, 40.0, 0.0, gate_m=200.0)
    assert pushed["speed_mps"] > plain["speed_mps"]
    assert pushed["t_gate_s"] < plain["t_gate_s"]
    assert pushed["v_release_mps"] is not None
    assert pushed["v_release_mps"] < 30.0


def pytest_approx(value, rel=None, abs=None):
    import pytest

    return pytest.approx(value, rel=rel, abs=abs)
