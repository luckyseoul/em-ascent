"""Pad twin versus tube handoff for one muzzle state."""

from __future__ import annotations

import math

from em_ascent.ascent import Vehicle, propellant_for_apogee, simulate_ascent
from em_ascent.constants import G0
from em_ascent.craft import (
    CD,
    DIAMETER_M,
    DRY_KG,
    ISP_S,
    PROP_KG,
    TW_GENTLE,
    TW_PAD,
)
from em_ascent.ignition import plan_light
from em_ascent.tube import TubeShot


def _vehicle(tw: float, prop: float = PROP_KG) -> Vehicle:
    wet = DRY_KG + prop
    return Vehicle(
        dry_kg=DRY_KG,
        prop_kg=prop,
        isp_s=ISP_S,
        diameter_m=DIAMETER_M,
        cd=CD,
        thrust_n=tw * wet * G0,
    )


def compare_flights(shot: TubeShot, target_apogee_m: float = 1000.0) -> list[dict]:
    gamma = float(shot.gamma[-1])
    v = float(shot.v[-1])
    clearance = plan_light(v).nominal_clearance_m
    rows = []
    missions = (
        (
            "tube, gentle motor",
            _vehicle(TW_GENTLE),
            float(shot.x[-1]),
            float(shot.h[-1]),
            v * math.cos(gamma),
            v * math.sin(gamma),
            clearance,
            0.0,
            TW_GENTLE,
        ),
        (
            "pad, same gentle motor",
            _vehicle(TW_GENTLE),
            0.0,
            0.3,
            0.4 * math.cos(gamma),
            0.4 * math.sin(gamma),
            0.0,
            2.0,
            TW_GENTLE,
        ),
        (
            "pad, high-thrust motor",
            _vehicle(TW_PAD),
            0.0,
            0.3,
            0.4 * math.cos(gamma),
            0.4 * math.sin(gamma),
            0.0,
            2.0,
            TW_PAD,
        ),
    )
    for name, vehicle, x0, h0, vx, vy, clearance, rail, tw in missions:
        flown = simulate_ascent(
            vehicle, x0, h0, vx, vy, gamma, clearance_m=clearance, rail_m=rail
        )
        prop = propellant_for_apogee(
            DRY_KG,
            ISP_S,
            DIAMETER_M,
            CD,
            tw,
            x0,
            h0,
            vx,
            vy,
            gamma,
            target_apogee_m,
            clearance_m=clearance,
            rail_m=rail,
            prop_hi=8.0,
        )
        rows.append(
            {
                "mission": name,
                "thrust_n": vehicle.thrust_n,
                "tw_ignition": vehicle.tw_ignition,
                "peak_motor_g": flown.peak_thrust_g,
                "apogee_m": flown.apogee_m,
                "t_gate_s": flown.t_gate_s,
                "peak_q_kpa": flown.peak_q_pa / 1000.0,
                "burnout_speed": flown.burnout_speed,
                "propellant_for_1km_kg": prop,
            }
        )
    return rows
