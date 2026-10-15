"""Emergency supply hops on the lunar surface.

The tube is on the Moon. Exit speed is set by bore length and acceleration,
not by mass. Coil energy and landing propellant scale with the thrown mass.
A chute is useless in vacuum. The base catches the package, or the package
kills its own speed with a small burn.
"""

from __future__ import annotations

import math

from em_ascent.constants import G0, G_MOON

# Structural acceleration is quoted in Earth g, same as the bore study.
# 14 Earth g is 137 m/s^2. It is a hard push and a short tube.
REFERENCE_LOAD_G = 14.0
REFERENCE_V_MPS = 110.0
REFERENCE_GAMMA_DEG = 45.0
# Coil bus to mechanical work. Same assumption as the Earth bore.
ETA_COIL = 0.20
# Monoprop-class landing burn. 110 m/s arrival plus margin for gravity loss
# and a few meters per second at touchdown.
LANDING_DV_MPS = 130.0
LANDING_ISP_S = 220.0
# Shell, sleeve, and a small thruster. 10% once the package is large enough
# that the 0.40 kg floor no longer dominates.
INERT_FRACTION = 0.10
INERT_FLOOR_KG = 0.40


def axial_accel(load_g: float) -> float:
    return load_g * G0


def tube_length(v_exit: float, load_g: float) -> float:
    """Straight-bore length for a commanded acceleration from rest."""
    return v_exit * v_exit / (2.0 * axial_accel(load_g))


def hop_range(v_exit: float, gamma_deg: float, g: float = G_MOON) -> float:
    """Flat-Moon range from muzzle to impact. Good inside a few tens of km."""
    return v_exit * v_exit * math.sin(math.radians(2.0 * gamma_deg)) / g


def hop_apex(v_exit: float, gamma_deg: float, g: float = G_MOON) -> float:
    vy = v_exit * math.sin(math.radians(gamma_deg))
    return vy * vy / (2.0 * g)


def speed_for_range(range_m: float, gamma_deg: float = 45.0, g: float = G_MOON) -> float:
    s = math.sin(math.radians(2.0 * gamma_deg))
    if s <= 0.0:
        raise ValueError("launch angle must produce a downrange hop")
    return math.sqrt(range_m * g / s)


def electrical_j_per_kg(v_exit: float, load_g: float, gamma_deg: float, eta: float = ETA_COIL) -> float:
    """Bank energy per kilogram of thrown mass, including the muzzle climb."""
    length = tube_length(v_exit, load_g)
    height = length * math.sin(math.radians(gamma_deg))
    specific = 0.5 * v_exit * v_exit + G_MOON * height
    return specific / eta


def peak_power_w_per_kg(v_exit: float, load_g: float, gamma_deg: float, eta: float = ETA_COIL) -> float:
    """Electrical power per kilogram at the muzzle, where force and speed peak."""
    force_per_kg = axial_accel(load_g) + G_MOON * math.sin(math.radians(gamma_deg))
    return force_per_kg * v_exit / eta


def landing_mass_fraction(dv_mps: float = LANDING_DV_MPS, isp_s: float = LANDING_ISP_S) -> float:
    """Mass still aboard after the landing burn, as a fraction of thrown mass."""
    return math.exp(-dv_mps / (isp_s * G0))


def supplies_kg(thrown_kg: float, catch: bool = False) -> float:
    """Supply mass inside a thrown package.

    `catch` means the base net or berm takes the arrival speed, so the package
    carries no landing propellant and no thruster. Otherwise the inert floor
    covers the shell and a small thruster, and the burn mass comes off the top.
    """
    if thrown_kg <= 0.0:
        raise ValueError("thrown mass must be positive")
    inert = max(INERT_FLOOR_KG, INERT_FRACTION * thrown_kg)
    if catch:
        # No thruster. Keep a shell, drop the thruster share of the floor.
        inert = max(0.30, 0.08 * thrown_kg)
        return max(0.0, thrown_kg - inert)
    final = thrown_kg * landing_mass_fraction()
    return max(0.0, final - inert)


def thrown_for_bank_j(bank_j: float, v_exit: float, load_g: float, gamma_deg: float) -> float:
    return bank_j / electrical_j_per_kg(v_exit, load_g, gamma_deg)
