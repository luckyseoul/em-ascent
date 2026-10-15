"""Engine-out landing cloud on the V100.

CuPy's CUDA 13 JIT does not build reductions for sm_70. This process uses the
cu124 PyTorch build, which already has V100 kernels. Run it with
`~/.venvs/torch-cu124/bin/python -m em_ascent.recovery_torch`.
"""

from __future__ import annotations

import json
import math
import sys
import time

import torch

from em_ascent.constants import G0


def _rho(h: torch.Tensor) -> torch.Tensor:
    h = h.clamp(0.0, 11000.0)
    temp = 288.15 - 0.0065 * h
    pressure = 101325.0 * (temp / 288.15) ** 5.25588
    return pressure / (287.05 * temp)


def fly(
    n: int,
    v_exit: float,
    gamma_deg: float,
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
) -> dict[str, torch.Tensor]:
    device = "cuda"
    g = torch.tensor(G0, device=device)
    gen = torch.Generator(device=device)
    gen.manual_seed(seed)
    gamma = math.radians(gamma_deg)
    wind_x = torch.randn(n, device=device, generator=gen) * wind_sigma
    wind_z = torch.randn(n, device=device, generator=gen) * wind_sigma
    vx = torch.full((n,), v_exit * math.cos(gamma), device=device) + wind_x
    vy = torch.full((n,), v_exit * math.sin(gamma), device=device)
    vz = wind_z
    x = torch.full((n,), x0, device=device)
    h = torch.full((n,), h0, device=device)
    z = torch.zeros(n, device=device)
    alive = torch.ones(n, dtype=torch.bool, device=device)
    h_max = h.clone()
    area_body = math.pi * 0.25 * diameter_m * diameter_m
    area_chute = 0.0 if not chute_diameter_m else math.pi * 0.25 * chute_diameter_m ** 2
    opened = torch.zeros(n, dtype=torch.bool, device=device)
    mass = torch.tensor(mass_kg, device=device)

    for _ in range(steps):
        if not bool(alive.any()):
            break
        rho = _rho(h)
        speed = torch.sqrt(vx * vx + vy * vy + vz * vz)
        if chute_diameter_m:
            opened = opened | (alive & (vy < 0.0))
            cd = torch.where(opened, torch.tensor(chute_cd, device=device), torch.tensor(cd_body, device=device))
            area = torch.where(
                opened,
                torch.tensor(area_chute, device=device),
                torch.tensor(area_body, device=device),
            )
        else:
            cd = cd_body
            area = area_body
        drag = 0.5 * rho * speed * speed * cd * area
        inv = 1.0 / torch.clamp(speed * mass, min=1e-6)
        ax = -drag * vx * inv
        ay = -g - drag * vy * inv
        az = -drag * vz * inv
        vx = torch.where(alive, vx + ax * dt, vx)
        vy = torch.where(alive, vy + ay * dt, vy)
        vz = torch.where(alive, vz + az * dt, vz)
        x = torch.where(alive, x + vx * dt, x)
        h = torch.where(alive, h + vy * dt, h)
        z = torch.where(alive, z + vz * dt, z)
        h_max = torch.maximum(h_max, h)
        alive = alive & (h > 0.0)

    speed_imp = torch.sqrt(vx * vx + vy * vy + vz * vz)
    return {"x": x, "z": z, "speed": speed_imp, "h_max": h_max}


def _summary(cloud: dict[str, torch.Tensor]) -> dict[str, float]:
    x = cloud["x"]
    z = cloud["z"]
    speed = cloud["speed"]
    h_max = cloud["h_max"]

    def pct(t: torch.Tensor, q: float) -> float:
        return float(torch.quantile(t, q).item())

    return {
        "n": int(x.shape[0]),
        "range_p50_m": pct(x, 0.50),
        "range_p05_m": pct(x, 0.05),
        "range_p95_m": pct(x, 0.95),
        "cross_p95_abs_m": pct(z.abs(), 0.95),
        "impact_speed_p50": pct(speed, 0.50),
        "impact_speed_p95": pct(speed, 0.95),
        "apogee_p50_m": pct(h_max, 0.50),
    }


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("CUDA torch is not available in this interpreter")
    payload = json.loads(sys.argv[1])
    n = int(payload["n"])
    common = dict(
        n=n,
        v_exit=float(payload["v_exit"]),
        gamma_deg=float(payload["gamma_deg"]),
        x0=float(payload["x0"]),
        h0=float(payload["h0"]),
        mass_kg=float(payload.get("mass_kg", 1.5)),
        diameter_m=float(payload.get("diameter_m", 0.07)),
        cd_body=float(payload.get("cd_body", 0.5)),
        wind_sigma=float(payload.get("wind_sigma", 2.0)),
        dt=0.01,
        steps=3500,
        seed=int(payload.get("seed", 7)),
    )
    torch.cuda.synchronize()
    free0, total = torch.cuda.mem_get_info()
    t0 = time.perf_counter()
    ballistic = fly(chute_diameter_m=None, chute_cd=1.5, **common)
    torch.cuda.synchronize()
    t1 = time.perf_counter()
    chute = fly(chute_diameter_m=float(payload.get("chute_diameter_m", 0.90)), chute_cd=1.5, **common)
    torch.cuda.synchronize()
    t2 = time.perf_counter()
    free1, _ = torch.cuda.mem_get_info()
    out = {
        "backend": "torch-cu124",
        "device": torch.cuda.get_device_name(0),
        "n": n,
        "ballistic_s": round(t1 - t0, 3),
        "chute_s": round(t2 - t1, 3),
        "mem_free_before_mib": free0 / (1024 * 1024),
        "mem_free_after_mib": free1 / (1024 * 1024),
        "mem_total_mib": total / (1024 * 1024),
        "ballistic": _summary(ballistic),
        "chute": _summary(chute),
    }
    json.dump(out, sys.stdout)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
