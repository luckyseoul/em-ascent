"""Presentation figures for a Starship pad retrofit. Numbers are the retrofit study."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Polygon

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "docs" / "figures"
BLUE = "#1f4e79"
RUST = "#b85c38"
GREEN = "#2f6f4e"
GOLD = "#c4a35a"
INK = "#1c1c1c"
PALE = "#f4f1ea"
STEEL = "#8d97a3"


def _canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(PALE)
    ax.set_facecolor(PALE)
    ax.set_title(title, color=INK, fontsize=14, pad=8, loc="left")
    return fig, ax


def pusher_ring():
    fig, ax = _canvas(10.5, 7.2, "Aft-skirt pusher ring on the existing mount")
    ax.add_patch(Rectangle((8, 8), 84, 3, facecolor="#c8c2b4", edgecolor=INK, lw=0.6))
    ax.text(50, 5.2, "Existing foundation and water-cooled steel plate", ha="center", va="center", fontsize=8, color=INK)
    # flame
    ax.add_patch(Polygon([[46, 11], [54, 11], [58, 22], [42, 22]], closed=True, facecolor="#e7d2b0", edgecolor=RUST, lw=0.4))
    # booster
    ax.add_patch(FancyBboxPatch((42, 22), 16, 58, boxstyle="round,pad=0.2,rounding_size=0.6", facecolor="#d5dbe3", edgecolor=BLUE, lw=1.4))
    ax.text(50, 78, "Super Heavy", ha="center", fontsize=9, color=BLUE)
    ax.text(50, 74, "9 m diameter", ha="center", fontsize=8, color=INK)
    # engines
    for x in (44.5, 47.5, 50.5, 53.5):
        ax.add_patch(Polygon([[x - 1.1, 22], [x + 1.1, 22], [x + 0.5, 16], [x - 0.5, 16]], closed=True, facecolor=STEEL, edgecolor=INK, lw=0.4))
    ax.text(64, 18, "33 Raptors\n80.8 MN", fontsize=8, color=INK, va="center")
    # shoes and stators
    ax.add_patch(Rectangle((36, 28), 6, 8, facecolor=GOLD, edgecolor=INK, lw=0.8))
    ax.add_patch(Rectangle((58, 28), 6, 8, facecolor=GOLD, edgecolor=INK, lw=0.8))
    ax.annotate("", xy=(39, 48), xytext=(39, 36), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.6))
    ax.annotate("", xy=(61, 48), xytext=(61, 36), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.6))
    ax.text(28, 42, "5 MN push\nthrough bolted shoes", fontsize=8, color=GREEN, ha="center")
    ax.plot([70, 70], [28, 68], color=RUST, lw=1.2)
    ax.plot([68.5, 71.5], [28, 28], color=RUST, lw=1.2)
    ax.plot([68.5, 71.5], [68, 68], color=RUST, lw=1.2)
    ax.text(76, 48, "40 m stroke\nthen the shoes\nrun off the motors", fontsize=8, color=RUST, va="center")
    ax.text(50, 90, "Shoes let go at 23 m/s    14.9 t left in the tanks    115 MW peak", ha="center", fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "pusher-ring.png", dpi=150)
    plt.close(fig)


def hold_down():
    fig, ax = _canvas(10.5, 6.2, "Powered stroke on the clamps that already hold the stack")
    ax.add_patch(Rectangle((10, 18), 80, 6, facecolor="#c8c2b4", edgecolor=INK, lw=0.6))
    ax.add_patch(Rectangle((28, 24), 44, 8, facecolor=STEEL, edgecolor=INK, lw=0.8))
    ax.text(50, 28, "Hold-down, a few meters of travel", ha="center", va="center", fontsize=8, color="white")
    ax.add_patch(FancyBboxPatch((38, 34), 24, 40, boxstyle="round,pad=0.2,rounding_size=0.5", facecolor="#d5dbe3", edgecolor=BLUE, lw=1.4))
    ax.text(50, 54, "Stack\n5,300 t", ha="center", va="center", fontsize=10, color=BLUE)
    ax.annotate("", xy=(50, 46), xytext=(50, 36), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.8))
    ax.text(8, 62, "Release becomes a shove\ninstead of a drop", fontsize=9, color=GREEN, ha="left")
    ax.text(78, 62, "10 m at 5 MN\nleaves 7.6 t\nplume leaves the plate sooner", fontsize=8, color=INK, ha="center")
    fig.tight_layout()
    fig.savefig(FIG / "hold-down.png", dpi=150)
    plt.close(fig)


def tower_rails():
    fig, ax = _canvas(10.5, 7.2, "Second pin set on the tower columns")
    ax.add_patch(Rectangle((18, 8), 8, 84, facecolor=STEEL, edgecolor=INK, lw=0.6))
    ax.text(22, 3.2, "Tower column, already built", ha="center", fontsize=8, color=INK)
    ax.add_patch(Rectangle((26, 16), 2.2, 62, facecolor=GOLD, edgecolor=INK, lw=0.4))
    ax.add_patch(FancyBboxPatch((36, 18), 18, 64, boxstyle="round,pad=0.15,rounding_size=0.4", facecolor="#d5dbe3", edgecolor=BLUE, lw=1.4))
    ax.text(45, 74, "Booster", ha="center", fontsize=9, color=BLUE)
    # grid fin pins high, short rail above
    ax.add_patch(Circle((35, 70), 1.3, facecolor=RUST, edgecolor=INK))
    ax.text(62, 70, "Catch pins stay for landing.\nLittle tower left above them.", fontsize=8, color=RUST, va="center")
    # lower pins
    ax.add_patch(Circle((35, 36), 1.5, facecolor=GREEN, edgecolor=INK))
    ax.annotate("", xy=(33, 52), xytext=(33, 36), arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.5))
    ax.text(62, 40, "New pins lower on the booster\nrun in a rail on the column.\nSame few-meganewton class.", fontsize=8, color=GREEN, va="center")
    ax.text(62, 16, "Chopsticks are not the pusher.\nThey catch an empty booster.", fontsize=8, color=INK, va="center")
    fig.tight_layout()
    fig.savefig(FIG / "tower-rails.png", dpi=150)
    plt.close(fig)


def fuel_chart():
    labels = ["10 m/s", "20 m/s", "50 m/s", "100 m/s"]
    tons = [45, 88, 205, 373]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    fig.patch.set_facecolor(PALE)
    ax.set_facecolor(PALE)
    colors = [BLUE, BLUE, GREEN, GOLD]
    ax.bar(labels, tons, color=colors)
    for i, value in enumerate(tons):
        ax.text(i, value + 6, f"{value} t", ha="center", va="bottom", fontsize=9, color=INK)
    ax.set_ylabel("Booster propellant left on the ground")
    ax.set_xlabel("Speed present at liftoff, same burnout, 5,300 t stack")
    ax.set_ylim(0, 430)
    ax.set_title("What that liftoff speed is worth in the integration")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "fuel-save.png", dpi=150)
    plt.close(fig)


def sim_fuel():
    import json

    rows = json.loads((ROOT / "data" / "starship_assist_grid.json").read_text())
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    fig.patch.set_facecolor(PALE)
    ax.set_facecolor(PALE)
    colors = {2.5: STEEL, 5.0: BLUE, 8.0: GREEN, 10.0: RUST, 15.0: GOLD}
    for force in (2.5, 5.0, 8.0, 10.0, 15.0):
        subset = [r for r in rows if r["assist_mn"] == force]
        subset.sort(key=lambda r: r["stroke_m"])
        ax.plot(
            [r["stroke_m"] for r in subset],
            [r["offload_t"] for r in subset],
            "o-",
            color=colors[force],
            label=f"{force:g} MN",
        )
    ax.scatter([40], [14.91], s=80, facecolors="none", edgecolors=INK, linewidths=1.4, zorder=5)
    ax.annotate("reference ring", xy=(40, 14.91), xytext=(48, 22), fontsize=8, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.7))
    ax.set_xlabel("Stroke along the mount (m)")
    ax.set_ylabel("Booster propellant left in the tanks (t)")
    ax.set_title("Same booster burnout speed, engines lit the whole way")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Pusher force", frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "sim-fuel.png", dpi=150)
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    pusher_ring()
    hold_down()
    tower_rails()
    fuel_chart()
    sim_fuel()
    print(FIG)


if __name__ == "__main__":
    main()
