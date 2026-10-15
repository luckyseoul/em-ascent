"""When the motor is allowed to light.

The abort is a clamped proof burn at the breech. The bore crossing is cold.
A position interlock keeps the jet out of the closed bore, and an open rail
holds the sleeve until chamber pressure has been seen.

Completely magnetic flight skips the motor. Go/no-go is then the coil bank
and the position encoders, before the barrel is released.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Valve-open to damaging thrust. Fast, nominal, and slow cover a small liquid or hybrid.
T_DELAY_FAST_S = 0.020
T_DELAY_NOMINAL_S = 0.050
T_DELAY_SLOW_S = 0.100
# Chamber-pressure bit after damaging thrust is unambiguous.
T_SENSE_S = 0.040
# Nozzle must be this far past the closed-bore mouth before the fire line is live.
SAFE_STATION_M = 0.25
# Extra open rail past the slow status station.
GUIDE_MARGIN_M = 0.50
# Proof burn into the breech bucket, then valves close before the coils move the craft.
PROOF_BURN_S = 0.40
PROOF_ABORT_S = 0.50


@dataclass(frozen=True)
class LightPlan:
    """Stations are meters past the closed-bore mouth, along the tube axis.

    Negative would be inside the coil bore. The interlock does not allow that.
    """

    v_exit: float
    safe_station_m: float
    thrust_fast_m: float
    thrust_nominal_m: float
    thrust_slow_m: float
    status_fast_m: float
    status_nominal_m: float
    status_slow_m: float
    open_guide_m: float

    @property
    def nominal_clearance_m(self) -> float:
        return self.thrust_nominal_m


def thrust_station(delay_s: float, v_exit: float, safe_station_m: float = SAFE_STATION_M) -> float:
    """Nozzle station when thrust becomes damaging.

    The fire line is armed at the safe station. The delay clock starts then,
    so a slow igniter lights farther out and a fast one still clears the bore.
    """
    if delay_s < 0.0:
        raise ValueError("ignition delay must be non-negative")
    return safe_station_m + v_exit * delay_s


def status_station(
    delay_s: float,
    v_exit: float,
    safe_station_m: float = SAFE_STATION_M,
    t_sense_s: float = T_SENSE_S,
) -> float:
    """Nozzle station when chamber pressure is a valid go/no-go bit."""
    return thrust_station(delay_s, v_exit, safe_station_m) + v_exit * t_sense_s


def plan_light(v_exit: float) -> LightPlan:
    fast = thrust_station(T_DELAY_FAST_S, v_exit)
    nominal = thrust_station(T_DELAY_NOMINAL_S, v_exit)
    slow = thrust_station(T_DELAY_SLOW_S, v_exit)
    status_slow = status_station(T_DELAY_SLOW_S, v_exit)
    return LightPlan(
        v_exit=v_exit,
        safe_station_m=SAFE_STATION_M,
        thrust_fast_m=fast,
        thrust_nominal_m=nominal,
        thrust_slow_m=slow,
        status_fast_m=status_station(T_DELAY_FAST_S, v_exit),
        status_nominal_m=status_station(T_DELAY_NOMINAL_S, v_exit),
        status_slow_m=status_slow,
        open_guide_m=status_slow + GUIDE_MARGIN_M,
    )


def timed_command_without_interlock(
    delay_s: float,
    v_exit: float,
    t_design_s: float = T_DELAY_NOMINAL_S,
    safe_station_m: float = SAFE_STATION_M,
) -> float:
    """Station of thrust if the command is a timer set for the nominal delay.

    A faster igniter than the timer lights inside the closed bore.
    """
    s_command = safe_station_m - v_exit * t_design_s
    return s_command + v_exit * delay_s


def sample_delay_risk(
    v_exit: float,
    n: int = 1_048_576,
    mean_s: float = T_DELAY_NOMINAL_S,
    sigma_s: float = 0.015,
    seed: int = 3,
) -> dict[str, float]:
    """Fraction of igniters that light inside the bore if the command is only a timer.

    One multiply and a reduction. It stays on the host. The landing cloud is the
    GPU job.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    delay = np.clip(rng.normal(mean_s, sigma_s, size=n), 0.005, 0.25).astype(np.float32)
    locked = np.float32(SAFE_STATION_M) + np.float32(v_exit) * delay
    s_command = SAFE_STATION_M - v_exit * T_DELAY_NOMINAL_S
    timed = np.float32(s_command) + np.float32(v_exit) * delay
    damage = timed < 0.0
    return {
        "n": n,
        "timer_damage_fraction": float(damage.mean()),
        "timer_thrust_p05_m": float(np.percentile(timed, 5)),
        "timer_thrust_p50_m": float(np.percentile(timed, 50)),
        "locked_thrust_p05_m": float(np.percentile(locked, 5)),
        "locked_thrust_p95_m": float(np.percentile(locked, 95)),
        "locked_min_m": float(locked.min()),
    }


def plume_radius_at_mouth(standoff_m: float, exit_radius_m: float, half_angle_deg: float) -> float:
    """Jet radius back at the coil mouth for a conical near-field plume."""
    return exit_radius_m + standoff_m * math.tan(math.radians(half_angle_deg))
