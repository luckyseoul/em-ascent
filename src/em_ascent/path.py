"""Launch-tube centerline.

The speed section is straight and steep. The direction change is a waterslide
at the breech: clothoid in, circular arc, clothoid out. Curvature starts at
zero, so the bore load does not step when the turn starts.

For a circular arc run at constant axial acceleration from rest, the normal
acceleration at the end of the turn is 2 * a_axial * delta_rad. Radius sets
the speed at which that ratio is reached. It does not set the ratio.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class TurnGeometry:
    gamma0_rad: float
    gamma1_rad: float
    radius_m: float
    blend_m: float
    s_const_m: float

    @property
    def s_turn_m(self) -> float:
        return self.s_const_m + 2.0 * self.blend_m

    @property
    def delta_rad(self) -> float:
        return self.gamma1_rad - self.gamma0_rad


def make_turn(
    gamma0_deg: float,
    gamma1_deg: float,
    radius_m: float,
    blend_m: float,
) -> TurnGeometry:
    if gamma1_deg <= gamma0_deg:
        raise ValueError("launch angle must be steeper than the breech angle")
    if radius_m <= 0.0:
        raise ValueError("turn radius must be positive")
    delta = math.radians(gamma1_deg - gamma0_deg)
    # Keep a real circular section. A pure clothoid pair is the limit case.
    blend = min(blend_m, 0.45 * radius_m * delta)
    blend = max(blend, 1e-4)
    s_const = radius_m * delta - blend
    if s_const <= 0.0:
        raise ValueError("turn radius and angle are too small for the blend")
    return TurnGeometry(
        gamma0_rad=math.radians(gamma0_deg),
        gamma1_rad=math.radians(gamma1_deg),
        radius_m=radius_m,
        blend_m=blend,
        s_const_m=s_const,
    )


def gamma_kappa(s_m: float, turn: TurnGeometry) -> tuple[float, float]:
    """Flight-path angle (rad) and curvature (1/m) at arc length s."""
    if s_m <= 0.0:
        return turn.gamma0_rad, 0.0
    radius = turn.radius_m
    blend = turn.blend_m
    s_const = turn.s_const_m
    s_entry = blend
    s_circ = blend + s_const
    s_exit = turn.s_turn_m
    if s_m < s_entry:
        kappa = (s_m / blend) / radius
        gamma = turn.gamma0_rad + (s_m * s_m) / (2.0 * blend * radius)
        return gamma, kappa
    if s_m < s_circ:
        gamma = turn.gamma0_rad + blend / (2.0 * radius) + (s_m - blend) / radius
        return gamma, 1.0 / radius
    if s_m < s_exit:
        u = s_m - s_circ
        kappa = (1.0 - u / blend) / radius
        dgamma = u / radius - (u * u) / (2.0 * blend * radius)
        gamma = (
            turn.gamma0_rad
            + blend / (2.0 * radius)
            + s_const / radius
            + dgamma
        )
        return gamma, kappa
    return turn.gamma1_rad, 0.0


def peak_normal_over_axial(delta_rad: float) -> float:
    """Normal/axial acceleration at the end of a constant-accel circular turn from rest."""
    return 2.0 * delta_rad
