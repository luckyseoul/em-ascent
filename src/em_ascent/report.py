"""Reference shot, flight comparison, and the two figures."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from em_ascent.constants import G0
from em_ascent.craft import ETA_COIL, LINER
from em_ascent.flights import compare_flights
from em_ascent.sweep import DATA
from em_ascent.tube import TubeSpec, simulate_tube

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "figures"


def spec_from_choice(choice: dict) -> TubeSpec:
    return TubeSpec(
        mass_kg=float(choice["mass_kg"]),
        v_exit=float(choice["v_exit_target"]),
        a_turn=float(choice["a_turn_g"]) * G0,
        a_barrel=float(choice["a_barrel_g"]) * G0,
        gamma0_deg=float(choice["gamma0_deg"]),
        gamma1_deg=float(choice["gamma1_deg"]),
        radius_m=float(choice["radius_m"]),
        eta_coil=ETA_COIL,
        liner=LINER,
    )


def write_profile(shot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    step = max(1, len(shot.t) // 400)
    idx = list(range(0, len(shot.t), step))
    if idx[-1] != len(shot.t) - 1:
        idx.append(len(shot.t) - 1)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["t_s", "s_m", "v_mps", "axial_g", "gamma_deg", "x_m", "h_m", "f_axial_n", "p_elec_kw", "n_wall_n"]
        )
        for i in idx:
            writer.writerow(
                [
                    f"{shot.t[i]:.6f}",
                    f"{shot.s[i]:.4f}",
                    f"{shot.v[i]:.4f}",
                    f"{shot.a[i] / G0:.4f}",
                    f"{math.degrees(shot.gamma[i]):.3f}",
                    f"{shot.x[i]:.4f}",
                    f"{shot.h[i]:.4f}",
                    f"{shot.f_axial[i]:.3f}",
                    f"{shot.p_elec[i] / 1000.0:.3f}",
                    f"{shot.n_wall[i]:.3f}",
                ]
            )


def write_figures(shot, flights: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIG.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((DATA / "geometry_map.csv").open()))
    family = [
        r
        for r in rows
        if float(r["v_exit_target"]) == 110.0
        and abs(float(r["gamma1_deg"]) - 65.0) < 0.1
        and abs(float(r["a_turn_g"]) - 3.0) < 0.1
        and abs(float(r["radius_m"]) - 1.5) < 0.05
    ]
    family.sort(key=lambda r: float(r["a_barrel_g"]))

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(
        [float(r["peak_axial_g"]) for r in family],
        [float(r["length_m"]) for r in family],
        "o-",
        color="#1f4e79",
    )
    ax.set_xlabel("Peak axial load in the barrel (g)")
    ax.set_ylabel("Tube length (m)")
    ax.set_title("110 m/s exit, 65° barrel, 3 g breech turn")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "length_vs_g.png", dpi=140)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    axes[0].plot(shot.s, shot.v, color="#1f4e79")
    axes[0].set_xlabel("Distance along the tube (m)")
    axes[0].set_ylabel("Speed (m/s)")
    axes[0].grid(True, alpha=0.3)
    axes[1].plot(shot.s, shot.a / G0, color="#1f4e79", label="axial")
    axes[1].plot(shot.s, shot.v**2 * shot.kappa / G0, color="#b85c38", label="normal")
    axes[1].set_xlabel("Distance along the tube (m)")
    axes[1].set_ylabel("Load factor (g)")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "reference_shot.png", dpi=140)
    plt.close(fig)

    # Trajectories are redrawn here so the ascent figure matches the table.
    from em_ascent.ascent import Vehicle, simulate_ascent
    from em_ascent.craft import CD, DIAMETER_M, DRY_KG, ISP_S, MUZZLE_CLEARANCE_M, PROP_KG, TW_GENTLE, TW_PAD

    gamma = float(shot.gamma[-1])
    v = float(shot.v[-1])
    specs = [
        ("tube, gentle motor", TW_GENTLE, float(shot.x[-1]), float(shot.h[-1]), v * math.cos(gamma), v * math.sin(gamma), MUZZLE_CLEARANCE_M, 0.0),
        ("pad, same motor", TW_GENTLE, 0.0, 0.3, 0.4 * math.cos(gamma), 0.4 * math.sin(gamma), 0.0, 2.0),
        ("pad, high thrust", TW_PAD, 0.0, 0.3, 0.4 * math.cos(gamma), 0.4 * math.sin(gamma), 0.0, 2.0),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for name, tw, x0, h0, vx, vy, clearance, rail in specs:
        wet = DRY_KG + PROP_KG
        vehicle = Vehicle(DRY_KG, PROP_KG, ISP_S, DIAMETER_M, CD, tw * wet * G0)
        flown = simulate_ascent(
            vehicle, x0, h0, vx, vy, gamma, clearance_m=clearance, rail_m=rail
        )
        ax.plot(flown.x, flown.h, label=name)
    ax.set_xlabel("Downrange (m)")
    ax.set_ylabel("Altitude (m)")
    ax.set_xlim(0, None)
    ax.set_ylim(0, None)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "ascent.png", dpi=140)
    plt.close(fig)
    _ = flights


def build_report() -> dict:
    choice = json.loads((DATA / "reference_choice.json").read_text())["choice"]
    shot = simulate_tube(spec_from_choice(choice))
    write_profile(shot, DATA / "reference_tube_profile.csv")
    flights = compare_flights(shot)
    (DATA / "flight_comparison.json").write_text(json.dumps(flights, indent=2) + "\n")
    write_figures(shot, flights)
    print(json.dumps(flights, indent=2))
    return {"choice": choice, "flights": flights, "feasible": shot.feasible}


def main() -> None:
    build_report()


if __name__ == "__main__":
    main()
