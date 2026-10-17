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


def test_leaving_the_fuel_behind_compounds():
    """The offload is a head start that grows. Full tanks only get the shove."""
    from em_ascent.starship_assist import propellant_to_match

    off = propellant_to_match(5.0e6, 40.0)["prop_offload_kg"]
    gate = 130_000.0
    plain = simulate(0.0, 0.0, 0.0, gate_m=gate, sample_s=2.0)
    full = simulate(5.0e6, 40.0, 0.0, gate_m=gate, sample_s=2.0)
    light = simulate(5.0e6, 40.0, off, gate_m=gate, sample_s=2.0)

    def height(flown, t):
        import numpy as np

        trace = flown["trace"]
        i = int(np.argmin(np.abs(trace["t"] - t)))
        return float(trace["h"][i])

    early = height(light, 20.0) - height(full, 20.0)
    late = height(light, 120.0) - height(full, 120.0)
    assert early > 0.0
    assert late > early * 5.0
    assert height(light, 120.0) - height(plain, 120.0) > height(full, 120.0) - height(plain, 120.0) + 200.0


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
