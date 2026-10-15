"""Tube-side spring-loaded ball transfers.

The balls are guides. They sit in the bore liner and roll on a rub strip on the
craft. The coils supply the axial force. A spring plunger with a fixed ball tip
would slide, so the hardware is a ball transfer: a ceramic ball free to spin,
preloaded by a spring or a polymer flexure in the wall.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Si3N4 ball. Nonmagnetic, so a coil pulse does not yank the guide.
SI3N4_E_PA = 310e9
SI3N4_NU = 0.27

# Hard rub strip on the craft. A magnetic steel race is the wrong default inside
# the bore. The number here is the elastic modulus of a hard nonmagnetic face
# (Nitronic-class or a ceramic strip). Aluminum and PEEK are the soft alternatives.
HARD_RACE_E_PA = 200e9
HARD_RACE_NU = 0.29
ALUMINUM_E_PA = 69e9
ALUMINUM_NU = 0.33
PEEK_E_PA = 3.6e9
PEEK_NU = 0.40


@dataclass(frozen=True)
class BallLiner:
    """Rings of inward-facing ball transfers in the tube wall."""

    n_around: int = 8
    n_lower: int = 3
    ring_pitch_m: float = 0.12
    sleeve_length_m: float = 0.30
    pad_length_m: float = 0.025
    ball_radius_m: float = 0.004
    preload_n: float = 6.0
    mu_roll: float = 0.006
    # Residual coil side-load as a fraction of axial force. The bore has to react it.
    radial_em_fraction: float = 0.05
    max_deflect_m: float = 0.0008

    @property
    def rings_on_sleeve(self) -> int:
        return max(1, math.ceil(self.sleeve_length_m / self.ring_pitch_m))

    @property
    def n_loaded(self) -> int:
        """Balls on the outer wall that share curvature and weight."""
        return self.rings_on_sleeve * self.n_lower

    @property
    def n_touching(self) -> int:
        return self.rings_on_sleeve * self.n_around


def reduced_modulus(e1: float, nu1: float, e2: float, nu2: float) -> float:
    return 1.0 / ((1.0 - nu1 * nu1) / e1 + (1.0 - nu2 * nu2) / e2)


def hertz_sphere_on_flat(force_n: float, radius_m: float, estar_pa: float) -> tuple[float, float]:
    """Return contact radius (m) and peak pressure (Pa) for a sphere on a flat."""
    if force_n <= 0.0:
        return 0.0, 0.0
    contact_radius = (3.0 * force_n * radius_m / (4.0 * estar_pa)) ** (1.0 / 3.0)
    pmax = 3.0 * force_n / (2.0 * math.pi * contact_radius * contact_radius)
    return contact_radius, pmax


def chordal_rise(radius_m: float, pad_length_m: float) -> float:
    """How far a straight rub pad lifts off a curved bore at mid-pad.

    A long rigid sleeve in a tight turn binds. Short pads keep the rise under
    the spring travel.
    """
    if radius_m <= 0.0:
        return 0.0
    return pad_length_m * pad_length_m / (8.0 * radius_m)


def ball_load(n_wall_n: float, liner: BallLiner) -> float:
    """Peak force on one loaded ball. Preload sits under the wall share."""
    return n_wall_n / liner.n_loaded + liner.preload_n


def spring_rate(peak_ball_n: float, liner: BallLiner) -> float:
    """Rate that reaches peak ball load at the allowed radial deflection."""
    return peak_ball_n / liner.max_deflect_m


def contact_report(peak_ball_n: float, liner: BallLiner) -> dict[str, float]:
    pairs = {
        "hard_race": reduced_modulus(SI3N4_E_PA, SI3N4_NU, HARD_RACE_E_PA, HARD_RACE_NU),
        "aluminum": reduced_modulus(SI3N4_E_PA, SI3N4_NU, ALUMINUM_E_PA, ALUMINUM_NU),
        "peek": reduced_modulus(SI3N4_E_PA, SI3N4_NU, PEEK_E_PA, PEEK_NU),
    }
    out = {"peak_ball_n": peak_ball_n, "spring_n_per_m": spring_rate(peak_ball_n, liner)}
    for name, estar in pairs.items():
        radius, pmax = hertz_sphere_on_flat(peak_ball_n, liner.ball_radius_m, estar)
        out[f"a_{name}_mm"] = radius * 1e3
        out[f"pmax_{name}_gpa"] = pmax / 1e9
    return out
