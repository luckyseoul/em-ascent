"""Engine-out and fully magnetic recovery.

A chute after apogee is the small-craft way to land with little damage.
A magnetic catch of a muzzle-speed vehicle is another tube. Catching near
apogee, after the vertical speed has died, is the short magnetic brake.
"""

from __future__ import annotations

import math

import numpy as np

from em_ascent.constants import G0

RHO_SEA = 1.225


def catch_stroke(speed_mps: float, load_g: float) -> float:
    """Distance to stop from `speed_mps` at a constant load factor."""
    if load_g <= 0.0:
        raise ValueError("catch load must be positive")
    return speed_mps * speed_mps / (2.0 * load_g * G0)


def chute_terminal_mps(mass_kg: float, diameter_m: float, cd: float = 1.5, rho: float = RHO_SEA) -> float:
    area = math.pi * 0.25 * diameter_m * diameter_m
    return math.sqrt(2.0 * mass_kg * G0 / (rho * cd * area))


def _rho(h, xp):
    h = xp.clip(h, 0.0, 11000.0)
    temp = 288.15 - 0.0065 * h
    pressure = 101325.0 * (temp / 288.15) ** 5.25588
    return pressure / (287.05 * temp)


def fly_cloud(
    *,
    n: int,
    v_exit: float,
    gamma_rad: float,
    x0: float,
    h0: float,
    mass_kg: float,
    diameter_m: float,
    cd_body: float,
    wind_sigma: float,
    chute_diameter_m: float | None,
    chute_cd: float,
    dt: float,
    steps: int,
    seed: int,
    xp,
):
    """Ballistic cloud. `xp` is numpy or cupy. Wind is horizontal, one draw per sample."""
    rng = xp.random.RandomState(seed) if hasattr(xp.random, "RandomState") else None
    if rng is None:
        gen = xp.random.default_rng(seed)
        wind_x = gen.normal(0.0, wind_sigma, size=n).astype(xp.float32)
        wind_z = gen.normal(0.0, wind_sigma, size=n).astype(xp.float32)
    else:
        wind_x = rng.normal(0.0, wind_sigma, size=n).astype(xp.float32)
        wind_z = rng.normal(0.0, wind_sigma, size=n).astype(xp.float32)

    vx = xp.full(n, v_exit * math.cos(gamma_rad), dtype=xp.float32) + wind_x
    vy = xp.full(n, v_exit * math.sin(gamma_rad), dtype=xp.float32)
    vz = wind_z
    x = xp.full(n, x0, dtype=xp.float32)
    h = xp.full(n, h0, dtype=xp.float32)
    z = xp.zeros(n, dtype=xp.float32)
    alive = xp.ones(n, dtype=xp.bool_)
    h_max = h.copy()
    area_body = math.pi * 0.25 * diameter_m * diameter_m
    area_chute = 0.0 if not chute_diameter_m else math.pi * 0.25 * chute_diameter_m ** 2
    opened = xp.zeros(n, dtype=xp.bool_)

    for _ in range(steps):
        if int(xp.count_nonzero(alive)) == 0:
            break
        rho = _rho(h, xp)
        speed = xp.sqrt(vx * vx + vy * vy + vz * vz)
        if chute_diameter_m:
            just = alive & (vy < 0.0) & ~opened
            opened = opened | just
            cd = xp.where(opened, xp.float32(chute_cd), xp.float32(cd_body))
            area = xp.where(opened, xp.float32(area_chute), xp.float32(area_body))
        else:
            cd = xp.float32(cd_body)
            area = xp.float32(area_body)
        drag = 0.5 * rho * speed * speed * cd * area
        inv = 1.0 / xp.maximum(speed * xp.float32(mass_kg), xp.float32(1e-6))
        ax = -drag * vx * inv
        ay = -xp.float32(G0) - drag * vy * inv
        az = -drag * vz * inv
        vx = xp.where(alive, vx + ax * dt, vx)
        vy = xp.where(alive, vy + ay * dt, vy)
        vz = xp.where(alive, vz + az * dt, vz)
        x = xp.where(alive, x + vx * dt, x)
        h = xp.where(alive, h + vy * dt, h)
        z = xp.where(alive, z + vz * dt, z)
        h_max = xp.maximum(h_max, h)
        alive = alive & (h > 0.0)

    speed_imp = xp.sqrt(vx * vx + vy * vy + vz * vz)
    return {
        "x": x,
        "z": z,
        "h": h,
        "h_max": h_max,
        "speed": speed_imp,
        "opened": opened,
    }


def summarize(cloud: dict, xp) -> dict[str, float]:
    x = cloud["x"]
    z = cloud["z"]
    speed = cloud["speed"]

    def pct(arr, q):
        value = xp.percentile(arr, q)
        return float(value.get() if hasattr(value, "get") else value)

    return {
        "n": int(x.shape[0]),
        "range_p50_m": pct(x, 50),
        "range_p05_m": pct(x, 5),
        "range_p95_m": pct(x, 95),
        "cross_p95_abs_m": pct(xp.abs(z), 95),
        "impact_speed_p50": pct(speed, 50),
        "impact_speed_p95": pct(speed, 95),
        "apogee_p50_m": pct(cloud["h_max"], 50),
    }


def cupy_available() -> bool:
    try:
        import cupy  # noqa: F401
    except ImportError:
        return False
    return True


def run_recovery_cloud(
    *,
    n: int = 1_048_576,
    v_exit: float,
    gamma_deg: float,
    x0: float,
    h0: float,
    mass_kg: float = 1.50,
    diameter_m: float = 0.070,
    cd_body: float = 0.50,
    wind_sigma: float = 2.0,
    chute_diameter_m: float = 0.90,
    seed: int = 7,
) -> dict:
    """Engine-out footprint and the same cloud with a chute. GPU when CuPy is present."""
    import cupy as cp

    cp.cuda.Device(0).use()
    # Touch the device so the run is not a host-side loop over a lazy graph.
    _ = cp.cuda.runtime.getDevice()
    gamma = math.radians(gamma_deg)
    common = dict(
        n=n,
        v_exit=v_exit,
        gamma_rad=gamma,
        x0=x0,
        h0=h0,
        mass_kg=mass_kg,
        diameter_m=diameter_m,
        cd_body=cd_body,
        wind_sigma=wind_sigma,
        dt=0.01,
        steps=3500,
        seed=seed,
        xp=cp,
    )
    free, _total = cp.cuda.runtime.memGetInfo()
    ballistic = fly_cloud(chute_diameter_m=None, chute_cd=1.5, **common)
    cp.cuda.Stream.null.synchronize()
    with_chute = fly_cloud(chute_diameter_m=chute_diameter_m, chute_cd=1.5, **common)
    cp.cuda.Stream.null.synchronize()
    used = cp.cuda.runtime.memGetInfo()
    return {
        "backend": "cupy",
        "device": "Tesla V100",
        "n": n,
        "mem_free_before_mib": free / (1024 * 1024),
        "mem_free_after_mib": used[0] / (1024 * 1024),
        "ballistic": summarize(ballistic, cp),
        "chute": summarize(with_chute, cp),
    }


def exit_speed_for_apogee(
    target_h_m: float,
    gamma_deg: float,
    h0: float,
    x0: float,
    v_lo: float = 80.0,
    v_hi: float = 400.0,
) -> float | None:
    """Exit speed whose no-wind ballistic apogee reaches `target_h_m`."""

    def apogee(speed: float) -> float:
        return numpy_one(speed, gamma_deg, x0, h0, chute_diameter_m=None)["apogee_m"]

    if apogee(v_hi) < target_h_m:
        return None
    for _ in range(18):
        mid = 0.5 * (v_lo + v_hi)
        if apogee(mid) >= target_h_m:
            v_hi = mid
        else:
            v_lo = mid
    return v_hi


def numpy_one(
    v_exit: float,
    gamma_deg: float,
    x0: float,
    h0: float,
    chute_diameter_m: float | None,
) -> dict[str, float]:
    """Single no-wind sample on the host, for checking the device cloud."""
    cloud = fly_cloud(
        n=1,
        v_exit=v_exit,
        gamma_rad=math.radians(gamma_deg),
        x0=x0,
        h0=h0,
        mass_kg=1.50,
        diameter_m=0.070,
        cd_body=0.50,
        wind_sigma=0.0,
        chute_diameter_m=chute_diameter_m,
        chute_cd=1.5,
        dt=0.01,
        steps=3500,
        seed=0,
        xp=np,
    )
    return {
        "range_m": float(cloud["x"][0]),
        "speed": float(cloud["speed"][0]),
        "apogee_m": float(cloud["h_max"][0]),
    }
