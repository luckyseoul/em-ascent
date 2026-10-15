"""Commanded-acceleration shot along the tube.

The coils are required to produce F_axial(s). The craft acceleration is the
input. Gravity, bore friction, and a residual radial coil load are the loads
the hardware has to supply or react.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from em_ascent.bearings import BallLiner, chordal_rise
from em_ascent.constants import G0
from em_ascent.path import TurnGeometry, gamma_kappa, make_turn


@dataclass(frozen=True)
class TubeSpec:
    mass_kg: float
    v_exit: float
    a_turn: float
    a_barrel: float
    gamma0_deg: float
    gamma1_deg: float
    radius_m: float
    blend_m: float = 0.30
    t_rise: float = 0.020
    t_exit: float = 0.030
    a_blend_m: float = 0.45
    eta_coil: float = 0.20
    liner: BallLiner = BallLiner()
    dt: float = 2.0e-4
    t_max: float = 12.0


@dataclass
class TubeShot:
    spec: TubeSpec
    turn: TurnGeometry
    t: np.ndarray
    s: np.ndarray
    v: np.ndarray
    a: np.ndarray
    gamma: np.ndarray
    kappa: np.ndarray
    x: np.ndarray
    h: np.ndarray
    f_axial: np.ndarray
    f_fric: np.ndarray
    n_wall: np.ndarray
    p_elec: np.ndarray
    feasible: bool
    exited_in_turn: bool
    reason: str

    @property
    def length_m(self) -> float:
        return float(self.s[-1])

    @property
    def muzzle_height_m(self) -> float:
        return float(self.h[-1])

    @property
    def peak_axial_g(self) -> float:
        return float(np.max(self.a) / G0)

    @property
    def peak_normal_g(self) -> float:
        normal = self.v * self.v * self.kappa
        return float(np.max(normal) / G0)


def _axial_force(
    mass: float,
    a: float,
    gamma: float,
    v: float,
    kappa: float,
    liner: BallLiner,
) -> tuple[float, float, float]:
    """Solve the small coupling between axial force and radial coil load.

    N_wall = N_kin + f * F_axial
    F_fric = mu * (N_wall + preload_sum)
    F_axial = m*a + m*g*sin(gamma) + F_fric
    """
    n_kin = mass * (v * v * kappa + G0 * math.cos(gamma))
    if n_kin < 0.0:
        n_kin = 0.0
    preload_sum = liner.n_touching * liner.preload_n
    f_ideal = mass * (a + G0 * math.sin(gamma))
    mu = liner.mu_roll
    frac = liner.radial_em_fraction
    denom = 1.0 - mu * frac
    if denom <= 0.05:
        raise ValueError("rolling friction and radial fraction leave no axial solution")
    f_axial = (f_ideal + mu * (n_kin + preload_sum)) / denom
    n_wall = n_kin + frac * f_axial
    f_fric = mu * (n_wall + preload_sum)
    return f_axial, f_fric, n_wall


def simulate_tube(spec: TubeSpec) -> TubeShot:
    turn = make_turn(spec.gamma0_deg, spec.gamma1_deg, spec.radius_m, spec.blend_m)
    liner = spec.liner
    mass = spec.mass_kg
    dt = spec.dt
    s_turn = turn.s_turn_m
    s_barrel_blend = s_turn + spec.a_blend_m

    t = 0.0
    s = 0.0
    v = 0.0
    x = 0.0
    h = 0.0
    exiting = False
    a_exit0 = 0.0
    t_exit0 = 0.0
    exited_in_turn = False

    ts: list[float] = []
    ss: list[float] = []
    vs: list[float] = []
    aas: list[float] = []
    gs: list[float] = []
    ks: list[float] = []
    xs: list[float] = []
    hs: list[float] = []
    fs: list[float] = []
    ffs: list[float] = []
    ns: list[float] = []
    ps: list[float] = []

    reason = "reached exit speed"
    feasible = True
    steps = 0
    max_steps = int(spec.t_max / dt) + 2

    while steps < max_steps:
        gamma, kappa = gamma_kappa(s, turn)
        if exiting:
            tau = t - t_exit0
            a = a_exit0 * max(0.0, 1.0 - tau / spec.t_exit)
        elif t < spec.t_rise:
            a = spec.a_turn * (t / spec.t_rise)
        elif s < s_turn:
            a = spec.a_turn
        elif s < s_barrel_blend:
            frac = (s - s_turn) / spec.a_blend_m
            a = spec.a_turn + frac * (spec.a_barrel - spec.a_turn)
        else:
            a = spec.a_barrel

        if not exiting and t > 0.5 * spec.t_rise:
            dv_ramp = 0.5 * a * spec.t_exit
            if v >= spec.v_exit - dv_ramp:
                exiting = True
                a_exit0 = a
                t_exit0 = t
                if s < s_turn:
                    exited_in_turn = True

        f_axial, f_fric, n_wall = _axial_force(mass, a, gamma, v, kappa, liner)
        p_elec = f_axial * v / spec.eta_coil

        ts.append(t)
        ss.append(s)
        vs.append(v)
        aas.append(a)
        gs.append(gamma)
        ks.append(kappa)
        xs.append(x)
        hs.append(h)
        fs.append(f_axial)
        ffs.append(f_fric)
        ns.append(n_wall)
        ps.append(p_elec)

        if exiting and (t - t_exit0) >= spec.t_exit:
            break

        v_new = v + a * dt
        if v_new < 0.0:
            v_new = 0.0
        ds = 0.5 * (v + v_new) * dt
        s_new = s + ds
        gamma_mid, _ = gamma_kappa(0.5 * (s + s_new), turn)
        x += ds * math.cos(gamma_mid)
        h += ds * math.sin(gamma_mid)
        v = v_new
        s = s_new
        t += dt
        steps += 1
    else:
        feasible = False
        reason = "shot did not reach the exit ramp before t_max"

    if abs(v - spec.v_exit) / spec.v_exit > 0.03:
        feasible = False
        reason = f"exit speed {v:.2f} m/s missed target {spec.v_exit:.2f}"
    if exited_in_turn:
        reason = "exit ramp started before the turn finished"

    shot = TubeShot(
        spec=spec,
        turn=turn,
        t=np.asarray(ts),
        s=np.asarray(ss),
        v=np.asarray(vs),
        a=np.asarray(aas),
        gamma=np.asarray(gs),
        kappa=np.asarray(ks),
        x=np.asarray(xs),
        h=np.asarray(hs),
        f_axial=np.asarray(fs),
        f_fric=np.asarray(ffs),
        n_wall=np.asarray(ns),
        p_elec=np.asarray(ps),
        feasible=feasible and not exited_in_turn,
        exited_in_turn=exited_in_turn,
        reason=reason,
    )
    return shot


def mechanical_energy_balance(shot: TubeShot) -> dict[str, float]:
    """∫ F ds against kinetic, potential, and bore-friction work."""
    work = float(np.trapezoid(shot.f_axial, shot.s))
    fric = float(np.trapezoid(shot.f_fric, shot.s))
    ke = 0.5 * shot.spec.mass_kg * float(shot.v[-1] ** 2 - shot.v[0] ** 2)
    pe = shot.spec.mass_kg * G0 * float(shot.h[-1] - shot.h[0])
    e_elec = float(np.trapezoid(shot.p_elec, shot.t))
    return {
        "work_j": work,
        "friction_j": fric,
        "ke_j": ke,
        "pe_j": pe,
        "ke_pe_fric_j": ke + pe + fric,
        "electrical_j": e_elec,
    }


def shot_scalars(shot: TubeShot) -> dict[str, float | int | bool | str]:
    energy = mechanical_energy_balance(shot)
    peak_ball = float(np.max(shot.n_wall) / shot.spec.liner.n_loaded + shot.spec.liner.preload_n)
    return {
        "mass_kg": shot.spec.mass_kg,
        "v_exit_target": shot.spec.v_exit,
        "a_turn_g": shot.spec.a_turn / G0,
        "a_barrel_g": shot.spec.a_barrel / G0,
        "gamma0_deg": shot.spec.gamma0_deg,
        "gamma1_deg": shot.spec.gamma1_deg,
        "radius_m": shot.spec.radius_m,
        "blend_m": shot.turn.blend_m,
        "turn_length_m": shot.turn.s_turn_m,
        "length_m": shot.length_m,
        "muzzle_x_m": float(shot.x[-1]),
        "muzzle_h_m": float(shot.h[-1]),
        "v_exit": float(shot.v[-1]),
        "t_shot_s": float(shot.t[-1]),
        "peak_axial_g": shot.peak_axial_g,
        "peak_normal_g": shot.peak_normal_g,
        "peak_force_n": float(np.max(shot.f_axial)),
        "peak_power_kw": float(np.max(shot.p_elec) / 1000.0),
        "energy_kj": energy["electrical_j"] / 1000.0,
        "work_kj": energy["work_j"] / 1000.0,
        "peak_wall_n": float(np.max(shot.n_wall)),
        "peak_ball_n": peak_ball,
        "chordal_rise_mm": chordal_rise(shot.spec.radius_m, shot.spec.liner.pad_length_m) * 1e3,
        "feasible": shot.feasible,
        "exited_in_turn": shot.exited_in_turn,
        "reason": shot.reason,
    }


def straight_length(v_exit: float, accel: float) -> float:
    """Constant acceleration from rest along a straight bore."""
    return v_exit * v_exit / (2.0 * accel)
