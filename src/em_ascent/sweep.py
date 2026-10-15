"""Geometry map for the launch tube.

Each case is an independent shot. The pool size is nproc-2. The V100 is the
wrong device: a case is a short sequential integration, not a dense batch.
"""

from __future__ import annotations

import csv
import itertools
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# One BLAS thread per worker. Set before NumPy is imported in this process.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_var] = "1"

from em_ascent.bearings import contact_report
from em_ascent.constants import G0
from em_ascent.craft import ETA_COIL, GAMMA0_DEG, LINER, WET_KG
from em_ascent.tube import TubeSpec, shot_scalars, simulate_tube

# Breech angle stays at GAMMA0. These four knobs are the tube.
GAMMA1_DEG = (45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0)
RADIUS_M = (1.5, 2.0, 2.5, 3.5, 5.0, 7.0, 10.0)
A_TURN_G = (3.0, 5.0, 7.0, 10.0, 14.0)
A_BARREL_G = (10.0, 14.0, 18.0, 22.0, 28.0, 36.0, 50.0, 70.0)
V_EXIT = (70.0, 90.0, 110.0, 130.0, 150.0)

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def default_workers() -> int:
    n = os.cpu_count() or 2
    return max(1, n - 2)


def iter_cases() -> list[dict[str, float]]:
    cases = []
    for gamma1, radius, a_turn_g, a_barrel_g, v_exit in itertools.product(
        GAMMA1_DEG, RADIUS_M, A_TURN_G, A_BARREL_G, V_EXIT
    ):
        cases.append(
            {
                "gamma1_deg": gamma1,
                "radius_m": radius,
                "a_turn_g": a_turn_g,
                "a_barrel_g": a_barrel_g,
                "v_exit": v_exit,
            }
        )
    return cases


def evaluate_case(case: dict[str, float]) -> dict:
    spec = TubeSpec(
        mass_kg=WET_KG,
        v_exit=case["v_exit"],
        a_turn=case["a_turn_g"] * G0,
        a_barrel=case["a_barrel_g"] * G0,
        gamma0_deg=GAMMA0_DEG,
        gamma1_deg=case["gamma1_deg"],
        radius_m=case["radius_m"],
        eta_coil=ETA_COIL,
        liner=LINER,
    )
    try:
        shot = simulate_tube(spec)
        row = shot_scalars(shot)
        row.update(contact_report(float(row["peak_ball_n"]), LINER))
    except ValueError as exc:
        row = dict(case)
        row["feasible"] = False
        row["reason"] = str(exc)
    row["feasible"] = bool(row.get("feasible", False))
    row["exited_in_turn"] = bool(row.get("exited_in_turn", False))
    return row


def select_reference(rows: list[dict]) -> dict | None:
    """Mildest barrel that still clears the breech turn inside a 50 m tube.

    Exit speed is fixed at 110 m/s so the table is one mission, not a mix.
    Launch angle is 65° or 75°. The curve load has to stay under the barrel load.
    """
    pool = []
    for row in rows:
        if not row.get("feasible") or row.get("exited_in_turn"):
            continue
        if float(row.get("v_exit_target", 0.0)) != 110.0:
            continue
        if float(row.get("gamma1_deg", 0.0)) < 65.0:
            continue
        if float(row.get("length_m", 1e9)) > 50.0:
            continue
        if float(row.get("peak_normal_g", 1e9)) > float(row["peak_axial_g"]) + 1.0:
            continue
        if float(row.get("pmax_hard_race_gpa", 99.0)) > 2.4:
            continue
        pool.append(row)
    if not pool:
        return None
    pool.sort(
        key=lambda r: (
            float(r["peak_axial_g"]),
            float(r["peak_normal_g"]),
            float(r["energy_kj"]),
            float(r["length_m"]),
        )
    )
    return pool[0]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def run_sweep(workers: int | None = None) -> tuple[list[dict], dict | None]:
    n = default_workers() if workers is None else workers
    cases = iter_cases()
    print(
        f"geometry map: {len(cases)} cases, {n} workers, serial-per-case kinematics",
        flush=True,
    )
    t0 = time.perf_counter()
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(evaluate_case, case) for case in cases]
        total = len(futures)
        for done, future in enumerate(as_completed(futures), start=1):
            rows.append(future.result())
            if done % 120 == 0 or done == total:
                print(f"geometry {done}/{total}", flush=True)
    rows.sort(
        key=lambda r: (
            float(r.get("v_exit_target", 0.0)),
            float(r.get("gamma1_deg", 0.0)),
            float(r.get("a_barrel_g", 0.0)),
            float(r.get("radius_m", 0.0)),
            float(r.get("a_turn_g", 0.0)),
        )
    )
    DATA.mkdir(parents=True, exist_ok=True)
    write_csv(DATA / "geometry_map.csv", rows)
    choice = select_reference(rows)
    payload = {
        "workers": n,
        "cases": len(rows),
        "feasible": sum(1 for r in rows if r.get("feasible")),
        "wall_s": round(time.perf_counter() - t0, 3),
        "choice": choice,
    }
    (DATA / "reference_choice.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"feasible {payload['feasible']}/{len(rows)}",
        flush=True,
    )
    return rows, choice


def main() -> None:
    run_sweep()


if __name__ == "__main__":
    main()
