"""Presentation figures for the short-notice small-payload cases."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from em_ascent.ascent import Vehicle, air_density, simulate_ascent
from em_ascent.constants import G0
from em_ascent.craft import CD, DIAMETER_M, DRY_KG, ISP_S, PROP_KG, TW_GENTLE, TW_PAD
from em_ascent.ignition import plan_light
from em_ascent.landing import fly_cloud
from em_ascent.sweep import DATA

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "figures"
BLUE = "#1f4e79"
RUST = "#b85c38"
GREEN = "#2f6f4e"
GOLD = "#c4a35a"
INK = "#1c1c1c"


def _shot_arrays():
    choice = json.loads((DATA / "reference_choice.json").read_text())["choice"]
    rows = np.genfromtxt(DATA / "reference_tube_profile.csv", delimiter=",", names=True)
    return choice, rows


def figure_layout(choice: dict, rows: np.ndarray) -> None:
    gamma = math.radians(float(choice["gamma1_deg"]))
    guide = plan_light(float(choice["v_exit"])).open_guide_m
    x = rows["x_m"]
    h = rows["h_m"]
    s = rows["s_m"]
    x_end = float(x[-1]) + guide * math.cos(gamma)
    h_end = float(h[-1]) + guide * math.sin(gamma)
    turn = s <= float(choice["turn_length_m"])

    fig, ax = plt.subplots(figsize=(10.2, 7.2))
    ax.plot(x[turn], h[turn], color=GOLD, lw=3.0, label="Breech turn, 3 g", solid_capstyle="round")
    ax.plot(x[~turn], h[~turn], color=BLUE, lw=3.0, label="Straight barrel, 14 g")
    ax.plot(
        [x[-1], x_end],
        [h[-1], h_end],
        color=GREEN,
        lw=3.0,
        ls=(0, (4, 2)),
        label="Open rail, motor lights here",
    )
    ax.scatter([x[0]], [h[0]], s=40, color=RUST, zorder=5)
    ax.annotate(
        "Clamp and proof burn\nFirst 1.8 m is the 3 g turn",
        xy=(float(x[0]), float(h[0])),
        xytext=(6, 10),
        fontsize=9,
        color=INK,
        arrowprops=dict(arrowstyle="->", color=INK, lw=0.8),
    )
    ax.annotate(
        "Muzzle, 110 m/s\n42 m up",
        xy=(x[-1], h[-1]),
        xytext=(x[-1] - 18, h[-1] - 12),
        fontsize=9,
        color=INK,
        arrowprops=dict(arrowstyle="->", color=INK, lw=0.8),
    )
    ax.annotate(
        "Pressure bit, still on the rail",
        xy=(x_end, h_end),
        xytext=(x_end - 22, h_end - 8),
        fontsize=9,
        color=INK,
        arrowprops=dict(arrowstyle="->", color=INK, lw=0.8),
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Downrange (m)")
    ax.set_ylabel("Height (m)")
    ax.set_title("Depot tube for a 1.5 kg package")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "layout.png", dpi=150)
    plt.close(fig)


def figure_sequence() -> None:
    """From a charged bank and a craft already on the clamp."""
    steps = [
        (0.0, 0.40, RUST, "Proof burn"),
        (0.40, 0.10, GOLD, "Valves shut"),
        (0.50, 1.12, BLUE, "Cold bore"),
        (1.62, 0.28, GREEN, "Light and status"),
    ]
    fig, ax = plt.subplots(figsize=(10.2, 2.6))
    for start, width, color, label in steps:
        ax.barh(0, width, left=start, height=0.55, color=color, edgecolor="white")
        ax.text(start + width / 2, 0, label, ha="center", va="center", color="white", fontsize=9)
    ax.set_xlim(0, 2.0)
    ax.set_yticks([])
    ax.set_xlabel("Seconds from the commit, bank already charged")
    ax.set_title("Short-notice sequence")
    ax.axvline(0.50, color=INK, lw=0.6, ls=":")
    ax.text(0.50, 0.48, "last abort", ha="center", va="bottom", fontsize=8, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "sequence.png", dpi=150)
    plt.close(fig)


def figure_compare() -> None:
    flights = json.loads((DATA / "flight_comparison.json").read_text())
    names = ["Tube beacon", "Pad, same motor", "Pad, high thrust"]
    apogee = [f["apogee_m"] / 1000 for f in flights]
    prop = [f["propellant_for_1km_kg"] for f in flights]
    motor_g = [f["peak_motor_g"] for f in flights]
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 3.8))
    colors = [BLUE, GOLD, RUST]
    panels = [
        (apogee, "Apogee on a 0.40 kg load (km)", False),
        (prop, "Propellant for a 1 km apogee (kg)", True),
        (motor_g, "Peak load on the motor (g)", False),
    ]
    for ax, (values, title, _log) in zip(axes, panels):
        ax.bar(names, values, color=colors)
        ax.set_title(title, fontsize=10)
        ax.tick_params(axis="x", labelrotation=15)
        ax.grid(True, axis="y", alpha=0.3)
        for i, value in enumerate(values):
            ax.text(i, value, f"{value:.2f}" if value < 20 else f"{value:.1f}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "compare.png", dpi=150)
    plt.close(fig)


def _one_path(chute: bool, v: float, gamma: float, x0: float, h0: float):
    dt = 0.02
    vx = v * math.cos(gamma)
    vy = v * math.sin(gamma)
    x, h = x0, h0
    xs, hs = [x], [h]
    area_body = math.pi * 0.25 * DIAMETER_M**2
    area_chute = math.pi * 0.25 * 0.90**2
    opened = False
    mass = 1.50
    for _ in range(4000):
        if h < 0 and len(xs) > 2:
            break
        speed = math.hypot(vx, vy)
        if chute and vy < 0:
            opened = True
        cd = 1.5 if opened else CD
        area = area_chute if opened else area_body
        rho = air_density(h)
        drag = 0.5 * rho * speed * speed * cd * area
        if speed > 1e-6:
            vx -= drag * vx / (speed * mass) * dt
            vy -= drag * vy / (speed * mass) * dt
        vy -= G0 * dt
        x += vx * dt
        h += vy * dt
        xs.append(x)
        hs.append(max(h, 0.0))
    return np.array(xs), np.array(hs)


def figure_paths(choice: dict) -> None:
    v = float(choice["v_exit"])
    gamma = math.radians(float(choice["gamma1_deg"]))
    x0 = float(choice["muzzle_x_m"])
    h0 = float(choice["muzzle_h_m"])
    vehicle = Vehicle(DRY_KG, PROP_KG, ISP_S, DIAMETER_M, CD, TW_GENTLE * (DRY_KG + PROP_KG) * G0)
    powered = simulate_ascent(
        vehicle,
        x0,
        h0,
        v * math.cos(gamma),
        v * math.sin(gamma),
        gamma,
        clearance_m=plan_light(v).nominal_clearance_m,
    )
    bare_x, bare_h = _one_path(False, v, gamma, x0, h0)
    chute_x, chute_h = _one_path(True, v, gamma, x0, h0)

    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    ax.plot(powered.x, powered.h, color=BLUE, lw=2.0, label="Beacon, motor lights (0.40 kg)")
    ax.plot(bare_x, bare_h, color=RUST, lw=1.6, label="Motor cold, no chute")
    ax.plot(chute_x, chute_h, color=GREEN, lw=2.0, label="Motor cold, 0.9 m chute")
    ax.axvspan(308, 346, color=GREEN, alpha=0.15, label="Chute recovery box, 95% downrange")
    ax.set_xlim(0, 2800)
    ax.set_ylim(0, 2600)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Downrange (m)")
    ax.set_ylabel("Altitude (m)")
    ax.set_title("Three ways the same 1.5 kg package leaves the tube")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "use_paths.png", dpi=150)
    plt.close(fig)


def figure_recovery(choice: dict) -> None:
    v = float(choice["v_exit"])
    gamma = math.radians(float(choice["gamma1_deg"]))
    cloud = fly_cloud(
        n=4000,
        v_exit=v,
        gamma_rad=gamma,
        x0=float(choice["muzzle_x_m"]),
        h0=float(choice["muzzle_h_m"]),
        mass_kg=1.50,
        diameter_m=DIAMETER_M,
        cd_body=CD,
        wind_sigma=2.0,
        chute_diameter_m=0.90,
        chute_cd=1.5,
        dt=0.02,
        steps=2500,
        seed=11,
        xp=np,
    )
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.scatter(cloud["x"], cloud["z"], s=6, c=GREEN, alpha=0.35, linewidths=0)
    ax.set_xlabel("Downrange (m)")
    ax.set_ylabel("Crossrange (m)")
    ax.set_title("Chute impacts, 4,000 engine-out samples, 2 m/s wind")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "recovery.png", dpi=150)
    plt.close(fig)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    choice, rows = _shot_arrays()
    figure_layout(choice, rows)
    figure_sequence()
    figure_compare()
    figure_paths(choice)
    figure_recovery(choice)
    print("wrote", FIG)


if __name__ == "__main__":
    main()
