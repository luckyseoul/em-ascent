"""Point-mass flight after the muzzle, and the pad-launch twin.

Thrust is along the velocity once the craft is moving. Before that it is along
the rail angle. Drag uses a troposphere density. No wind, no lift.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from em_ascent.constants import (
    G0,
    H_TROPOPAUSE,
    LAPSE,
    P0,
    P_TROPOPAUSE,
    R_SPECIFIC_AIR,
    T0,
    T_TROPOPAUSE,
)


def air_density(height_m: float) -> float:
    h = min(max(height_m, 0.0), 40_000.0)
    if h <= H_TROPOPAUSE:
        temp = T0 - LAPSE * h
        pressure = P0 * (temp / T0) ** (G0 / (LAPSE * R_SPECIFIC_AIR))
    else:
        temp = T_TROPOPAUSE
        pressure = P_TROPOPAUSE * math.exp(
            -G0 * (h - H_TROPOPAUSE) / (R_SPECIFIC_AIR * temp)
        )
    return pressure / (R_SPECIFIC_AIR * temp)


@dataclass(frozen=True)
class Vehicle:
    dry_kg: float
    prop_kg: float
    isp_s: float
    diameter_m: float
    cd: float
    thrust_n: float

    @property
    def wet_kg(self) -> float:
        return self.dry_kg + self.prop_kg

    @property
    def area_m2(self) -> float:
        return math.pi * 0.25 * self.diameter_m * self.diameter_m

    @property
    def tw_ignition(self) -> float:
        return self.thrust_n / (self.wet_kg * G0)

    @property
    def burnout_g(self) -> float:
        """Axial load factor at burnout for constant thrust."""
        return self.thrust_n / (self.dry_kg * G0)


@dataclass(frozen=True)
class AscentResult:
    apogee_m: float
    apogee_x_m: float
    t_apogee_s: float
    burnout_speed: float
    propellant_burned_kg: float
    peak_q_pa: float
    peak_thrust_g: float
    t_gate_s: float | None
    x: np.ndarray
    h: np.ndarray
    v: np.ndarray


def _ride_rail(
    vehicle: Vehicle,
    x0: float,
    h0: float,
    v0: float,
    gamma_rad: float,
    rail_m: float,
) -> tuple[float, float, float, float, float, float, list[float], list[float]]:
    """Hold heading until `rail_m` of travel. A slow gravity turn otherwise digs in."""
    ux = math.cos(gamma_rad)
    uy = math.sin(gamma_rad)
    v = max(v0, 0.0)
    s = 0.0
    mass = vehicle.wet_kg
    t = 0.0
    dt = 0.001
    thrust = vehicle.thrust_n
    mdot = thrust / (vehicle.isp_s * G0) if thrust > 0.0 else 0.0
    xs = [x0]
    hs = [h0]
    while s < rail_m - 1e-9 and t < 40.0:
        h = h0 + s * uy
        rho = air_density(h)
        drag = 0.5 * rho * v * v * vehicle.cd * vehicle.area_m2
        along = -G0 * uy
        if thrust > 0.0 and mass > vehicle.dry_kg + 1e-9:
            along += thrust / mass
            mass_dot = mdot
        else:
            mass_dot = 0.0
        if v > 0.0 or along > 0.0:
            along -= drag / mass
        v_new = v + along * dt
        if v_new < 0.0:
            v_new = 0.0
        ds = 0.5 * (v + v_new) * dt
        if s + ds > rail_m:
            scale = (rail_m - s) / ds if ds > 0.0 else 1.0
            ds *= scale
            v_new = v + (v_new - v) * scale
            dt_use = dt * scale
        else:
            dt_use = dt
        s += ds
        v = v_new
        mass = max(vehicle.dry_kg, mass - mass_dot * dt_use)
        t += dt_use
        xs.append(x0 + s * ux)
        hs.append(h0 + s * uy)
        if v <= 0.0 and along <= 0.0:
            break
    return t, x0 + s * ux, h0 + s * uy, v * ux, v * uy, mass, xs, hs


def simulate_ascent(
    vehicle: Vehicle,
    x0: float,
    h0: float,
    vx0: float,
    vy0: float,
    gamma_rad: float,
    clearance_m: float = 0.0,
    rail_m: float = 0.0,
    t_max: float = 90.0,
    gate_h_m: float = 80.0,
    gate_v_mps: float = 70.0,
) -> AscentResult:
    """Fly until vertical speed goes negative. `clearance_m` delays ignition."""

    area = vehicle.area_m2
    cd = vehicle.cd
    thrust = vehicle.thrust_n
    isp = vehicle.isp_s
    dry = vehicle.dry_kg
    mdot = thrust / (isp * G0) if thrust > 0.0 else 0.0
    t_rail = 0.0
    rail_x: list[float] = []
    rail_h: list[float] = []
    mass0 = vehicle.wet_kg
    if rail_m > 0.0:
        v0 = math.hypot(vx0, vy0)
        t_rail, x0, h0, vx0, vy0, mass0, rail_x, rail_h = _ride_rail(
            vehicle, x0, h0, v0, gamma_rad, rail_m
        )
    x_muzzle = x0 - rail_m * math.cos(gamma_rad) if rail_m > 0.0 else x0
    h_muzzle = h0 - rail_m * math.sin(gamma_rad) if rail_m > 0.0 else h0

    def deriv(_t: float, y: np.ndarray) -> list[float]:
        x, h, vx, vy, mass = y
        speed = math.hypot(vx, vy)
        rho = air_density(h)
        drag = 0.5 * rho * speed * speed * cd * area
        if speed >= 3.0:
            ux = vx / speed
            uy = vy / speed
        else:
            ux = math.cos(gamma_rad)
            uy = math.sin(gamma_rad)
        dist = math.hypot(x - x_muzzle, h - h_muzzle)
        burning = thrust > 0.0 and mass > dry + 1e-6 and dist >= clearance_m
        ax = 0.0
        ay = -G0
        if speed > 1e-8:
            ax -= drag * vx / (speed * mass) if speed >= 3.0 else drag * ux / mass
            ay -= drag * vy / (speed * mass) if speed >= 3.0 else drag * uy / mass
        if burning:
            ax += thrust * ux / mass
            ay += thrust * uy / mass
            return [vx, vy, ax, ay, -mdot]
        return [vx, vy, ax, ay, 0.0]

    def descending(_t: float, y: np.ndarray) -> float:
        return y[3]

    descending.terminal = True
    descending.direction = -1

    def underground(_t: float, y: np.ndarray) -> float:
        return y[1]

    underground.terminal = True
    underground.direction = -1

    sol = solve_ivp(
        deriv,
        (0.0, t_max),
        (x0, h0, vx0, vy0, mass0),
        method="RK45",
        max_step=0.02,
        rtol=1e-6,
        atol=1e-8,
        events=[descending, underground],
    )
    x = sol.y[0]
    h = sol.y[1]
    vx = sol.y[2]
    vy = sol.y[3]
    mass = sol.y[4]
    speed = np.hypot(vx, vy)
    idx = int(np.argmax(h))
    # Dynamic pressure along the trace.
    q = np.array(
        [0.5 * air_density(float(hi)) * float(vi) ** 2 for hi, vi in zip(h, speed)],
        dtype=float,
    )
    t_gate = None
    for ti, hi, vi, vyi in zip(sol.t, h, speed, vy):
        if hi >= gate_h_m and vi >= gate_v_mps and vyi > 0.0:
            t_gate = float(ti) + t_rail
            break
    burned = float(vehicle.wet_kg - float(mass[idx]))
    # Burnout speed: first sample at dry mass, else the apogee sample.
    burn_idx = idx
    for i, mi in enumerate(mass):
        if mi <= dry + 1e-4:
            burn_idx = i
            break
    lightest = float(np.min(mass[: idx + 1]))
    peak_g = thrust / (lightest * G0) if thrust > 0.0 else 0.0
    return AscentResult(
        apogee_m=float(h[idx]),
        apogee_x_m=float(x[idx]),
        t_apogee_s=float(sol.t[idx]) + t_rail,
        burnout_speed=float(speed[burn_idx]),
        propellant_burned_kg=max(0.0, burned),
        peak_q_pa=float(np.max(q)),
        peak_thrust_g=peak_g,
        t_gate_s=t_gate,
        x=np.concatenate([rail_x, x]) if rail_x else x,
        h=np.concatenate([rail_h, h]) if rail_h else h,
        v=speed,
    )


def propellant_for_apogee(
    dry_kg: float,
    isp_s: float,
    diameter_m: float,
    cd: float,
    tw: float,
    x0: float,
    h0: float,
    vx0: float,
    vy0: float,
    gamma_rad: float,
    target_h_m: float,
    clearance_m: float = 0.0,
    rail_m: float = 0.0,
    prop_hi: float = 2.5,
) -> float | None:
    """Smallest propellant load that reaches `target_h_m` at this liftoff T/W."""

    def apogee(prop: float) -> float:
        wet = dry_kg + prop
        vehicle = Vehicle(
            dry_kg=dry_kg,
            prop_kg=prop,
            isp_s=isp_s,
            diameter_m=diameter_m,
            cd=cd,
            thrust_n=tw * wet * G0,
        )
        return simulate_ascent(
            vehicle, x0, h0, vx0, vy0, gamma_rad, clearance_m=clearance_m, rail_m=rail_m
        ).apogee_m

    if apogee(prop_hi) < target_h_m:
        return None
    lo = 0.02
    hi = prop_hi
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if apogee(mid) >= target_h_m:
            hi = mid
        else:
            lo = mid
    return hi
