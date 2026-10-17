"""Liftoff of a Block 3 stack with a pad pusher still on the mount.

The engines fly the rocket. The pusher adds a vertical force for a short
stroke and then lets go. Propellant saved is the booster load you can leave
in the tanks and still match the unassisted speed at the gate altitude.
"""

from __future__ import annotations

import json
import math
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

from em_ascent.ascent import air_density
from em_ascent.constants import G0, P0

# Block 3 public liftoff. Booster dry mass is not published for Block 3.
# 275 t is the Block 1 figure. It is not used here: the ship stays full,
# so only booster propellant changes.
GLOW_KG = 5_300_000.0
BOOSTER_PROP_KG = 3_650_000.0
THRUST_SL_N = 80.8e6
ISP_SL_S = 327.0
ISP_VAC_S = 350.0
DIAMETER_M = 9.0
CD = 0.45
GATE_M = 10_000.0
# Vertical through the mount. Pitch follows altitude so both rockets
# have the same flight-path angle at the same height.
PITCH_H0 = 200.0
PITCH_H1 = 8_000.0
PITCH_END_DEG = 65.0

MDOT = THRUST_SL_N / (ISP_SL_S * G0)
AREA = math.pi * 0.25 * DIAMETER_M * DIAMETER_M


def pitch_deg(height_m: float) -> float:
    if height_m <= PITCH_H0:
        return 90.0
    if height_m >= PITCH_H1:
        return PITCH_END_DEG
    frac = (height_m - PITCH_H0) / (PITCH_H1 - PITCH_H0)
    return 90.0 + frac * (PITCH_END_DEG - 90.0)


def simulate(
    assist_n: float = 0.0,
    stroke_m: float = 0.0,
    prop_offload_kg: float = 0.0,
    gate_m: float | None = None,
    sample_s: float | None = None,
) -> dict:
    """Fly to booster burnout, or to `gate_m` if that is set.

    Assist is vertical and only while height is inside the stroke.
    """
    if prop_offload_kg < 0.0 or prop_offload_kg >= BOOSTER_PROP_KG:
        raise ValueError("propellant offload is outside the booster load")
    m0 = GLOW_KG - prop_offload_kg
    m_dry_boost = GLOW_KG - BOOSTER_PROP_KG

    def deriv(t: float, y: np.ndarray) -> list[float]:
        x, h, vx, vy, mass = y
        if mass <= m_dry_boost:
            return [vx, vy, 0.0, -G0, 0.0]
        rho = air_density(h)
        # Sea-level thrust scales toward vacuum as ambient pressure falls.
        pressure_ratio = 0.0
        if h < 20_000.0:
            # Density ratio is a decent stand-in for p/p0 in the troposphere.
            pressure_ratio = min(1.0, rho * 287.05 * (288.15 - 0.0065 * max(h, 0.0)) / P0)
        thrust = THRUST_SL_N + (MDOT * ISP_VAC_S * G0 - THRUST_SL_N) * (1.0 - pressure_ratio)
        gamma = math.radians(pitch_deg(h))
        ax = thrust * math.cos(gamma) / mass
        ay = thrust * math.sin(gamma) / mass - G0
        if h < stroke_m and assist_n > 0.0:
            ay += assist_n / mass
        speed = math.hypot(vx, vy)
        if speed > 1.0 and rho > 0.0:
            drag = 0.5 * rho * speed * speed * CD * AREA
            ax -= drag * vx / (speed * mass)
            ay -= drag * vy / (speed * mass)
        return [vx, vy, ax, ay, -MDOT]

    def at_meco(_t: float, y: np.ndarray) -> float:
        return y[4] - m_dry_boost

    at_meco.terminal = True
    at_meco.direction = -1

    def at_gate(_t: float, y: np.ndarray) -> float:
        return y[1] - (gate_m if gate_m is not None else 1.0e9)

    at_gate.terminal = True
    at_gate.direction = 1

    sol = solve_ivp(
        deriv,
        (0.0, 250.0),
        (0.0, 0.0, 0.0, 0.0, m0),
        events=[at_meco, at_gate],
        method="RK45",
        rtol=1e-6,
        atol=1e-6,
        max_step=0.1,
        dense_output=True,
    )
    t_gate = float(sol.t[-1])
    for events in sol.t_events:
        if events.size:
            t_gate = min(t_gate, float(events[0]))
    x, h, vx, vy, mass = sol.sol(t_gate)
    # Shoe release: first time height reaches the stroke, if there is one.
    t_release = None
    v_release = None
    if stroke_m > 0.0 and sol.sol is not None:
        times = np.linspace(0.0, t_gate, 400)
        heights = sol.sol(times)[1]
        idx = int(np.argmax(heights >= stroke_m))
        if heights[idx] >= stroke_m:
            t_release = float(times[idx])
            state = sol.sol(t_release)
            v_release = float(math.hypot(state[2], state[3]))
    speed = float(math.hypot(vx, vy))
    trace = None
    if sample_s and sol.sol is not None:
        ts = np.arange(0.0, max(t_gate, sample_s), sample_s)
        ts = ts[ts <= t_gate + 1e-9]
        st = sol.sol(ts)
        trace = {
            "t": ts,
            "h": st[1],
            "v": np.hypot(st[2], st[3]),
        }
    return {
        "t_gate_s": t_gate,
        "speed_mps": speed,
        "altitude_m": float(h),
        "downrange_m": float(x),
        "mass_kg": float(mass),
        "prop_burned_kg": m0 - float(mass),
        "prop_offload_kg": prop_offload_kg,
        "t_release_s": t_release,
        "v_release_mps": v_release,
        "liftoff_tw": (THRUST_SL_N + assist_n) / (m0 * G0),
        "trace": trace,
    }


def propellant_to_match(assist_n: float, stroke_m: float, gate_m: float | None = None) -> dict:
    """Largest booster offload that still matches the unassisted speed."""
    baseline = simulate(0.0, 0.0, 0.0, gate_m)
    target = baseline["speed_mps"]

    def speed(offload: float) -> float:
        return simulate(assist_n, stroke_m, offload, gate_m)["speed_mps"]

    if speed(0.0) < target:
        return {**baseline, "assist_n": assist_n, "stroke_m": stroke_m, "matched": False}
    lo = 0.0
    hi = 200_000.0
    if speed(hi) > target:
        hi = 800_000.0
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        if speed(mid) >= target:
            lo = mid
        else:
            hi = mid
    flown = simulate(assist_n, stroke_m, lo, gate_m)
    flown.update(
        {
            "assist_n": assist_n,
            "stroke_m": stroke_m,
            "baseline_speed_mps": target,
            "baseline_t_gate_s": baseline["t_gate_s"],
            "matched": True,
            "lox_t": lo / 1000.0 * 3.62 / 4.62,
            "ch4_t": lo / 1000.0 * 1.00 / 4.62,
        }
    )
    return flown


def _worker(job: tuple[float, float]) -> dict:
    force, stroke = job
    row = propellant_to_match(force, stroke)
    row["assist_mn"] = force / 1e6
    return row


def default_workers() -> int:
    n = os.cpu_count() or 2
    return max(1, n - 2)


def run_grid(workers: int | None = None) -> list[dict]:
    """Independent liftoff cases. One trajectory each, so this is a process pool."""
    forces = (2.5e6, 5.0e6, 8.0e6, 10.0e6, 15.0e6)
    strokes = (10.0, 20.0, 40.0, 60.0, 100.0)
    jobs = [(f, s) for f in forces for s in strokes]
    n = default_workers() if workers is None else workers
    # Each integration is one ODE. The grid is independent, so fan out.
    # Fork, not forkserver: the jobs are functions in this module, and a
    # forkserver has nothing to import when the driver is stdin.
    ctx = mp.get_context("fork")
    with ProcessPoolExecutor(max_workers=min(n, len(jobs)), mp_context=ctx) as pool:
        rows = list(pool.map(_worker, jobs))
    rows.sort(key=lambda r: (r["assist_mn"], r["stroke_m"]))
    return rows


def write_grid(path: Path | None = None, workers: int | None = None) -> list[dict]:
    rows = run_grid(workers)
    slim = []
    for row in rows:
        slim.append(
            {
                "assist_mn": row["assist_mn"],
                "stroke_m": row["stroke_m"],
                "offload_t": round(row["prop_offload_kg"] / 1000.0, 2),
                "lox_t": round(row.get("lox_t", 0.0), 2),
                "ch4_t": round(row.get("ch4_t", 0.0), 2),
                "v_release_mps": None
                if row["v_release_mps"] is None
                else round(row["v_release_mps"], 2),
                "t_release_s": None if row["t_release_s"] is None else round(row["t_release_s"], 2),
                "meco_mps": round(row["speed_mps"], 1),
                "matched": row["matched"],
            }
        )
    dest = path or Path(__file__).resolve().parents[2] / "data" / "starship_assist_grid.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(slim, indent=2) + "\n")
    return slim


if __name__ == "__main__":
    found = write_grid()
    for row in found:
        print(
            f"{row['assist_mn']:5.1f} MN  {row['stroke_m']:5.0f} m  "
            f"{row['offload_t']:6.2f} t  release {row['v_release_mps']} m/s"
        )
