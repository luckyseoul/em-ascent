import pytest

from em_ascent.ignition import (
    SAFE_STATION_M,
    T_DELAY_FAST_S,
    T_DELAY_SLOW_S,
    plan_light,
    plume_radius_at_mouth,
    thrust_station,
    timed_command_without_interlock,
)


def test_interlock_never_lights_inside_the_bore():
    plan = plan_light(110.0)
    for delay in (0.0, T_DELAY_FAST_S, 0.05, T_DELAY_SLOW_S, 0.2):
        assert thrust_station(delay, 110.0) >= SAFE_STATION_M
    assert plan.thrust_fast_m >= plan.safe_station_m
    assert plan.open_guide_m > plan.status_slow_m


def test_timer_without_interlock_lights_early_inside_the_bore():
    early = timed_command_without_interlock(T_DELAY_FAST_S, 110.0)
    assert early < 0.0


def test_nominal_onset_is_the_safe_station_plus_the_delay_distance():
    v = 110.0
    assert thrust_station(0.05, v) == pytest.approx(SAFE_STATION_M + v * 0.05)


def test_fast_plume_reaches_a_mouth_deflector():
    plan = plan_light(110.0)
    radius = plume_radius_at_mouth(plan.thrust_fast_m, exit_radius_m=0.012, half_angle_deg=20.0)
    assert radius > 0.05
