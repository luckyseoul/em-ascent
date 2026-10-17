"""Vector frames of the first seconds: engines only, ring with full tanks, ring with the saved fuel left behind."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from em_ascent.starship_assist import propellant_to_match, simulate

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "figures"
STROKE_M = 40.0
ASSIST_N = 5.0e6
DURATION_S = 5.0
FPS = 12
VIEW_M = 110.0


def _traces():
    offload = propellant_to_match(ASSIST_N, STROKE_M)["prop_offload_kg"]
    gate = VIEW_M + 15.0
    plain = simulate(0.0, 0.0, 0.0, gate_m=gate, sample_s=1.0 / FPS)
    full = simulate(ASSIST_N, STROKE_M, 0.0, gate_m=gate, sample_s=1.0 / FPS)
    light = simulate(ASSIST_N, STROKE_M, offload, gate_m=gate, sample_s=1.0 / FPS)
    n = min(len(plain["trace"]["t"]), len(full["trace"]["t"]), len(light["trace"]["t"]))
    n = min(n, int(DURATION_S * FPS) + 1)
    return plain["trace"], full["trace"], light["trace"], offload, n


def _frame(i: int, plain: dict, full: dict, light: dict, offload_kg: float) -> str:
    t = float(plain["t"][i])
    h0 = float(plain["h"][i])
    h1 = float(full["h"][i])
    h2 = float(light["h"][i])
    v0 = float(plain["v"][i])
    v1 = float(full["v"][i])
    v2 = float(light["v"][i])
    # Pad at y=640. 70 m of air maps to 520 px.
    scale = 500.0 / VIEW_M
    ground = 620.0
    pad = ground + 22.0

    def y_of(height: float) -> float:
        return ground - height * scale

    engaged = h1 < STROKE_M
    clock = f"{t:0.2f} s"
    offload_t = offload_kg / 1000.0

    def booster(cx: float, height: float, shoes: bool, pushing: bool) -> str:
        top = y_of(height + 46.0)
        base = y_of(height)
        parts = [
            f'<rect x="{cx - 28}" y="{top:.1f}" width="56" height="{base - top:.1f}" rx="3" fill="#c5ced8" stroke="#1f4e79" stroke-width="2"/>',
        ]
        for k, dx in enumerate((-18, -6, 6, 18)):
            parts.append(
                f'<polygon points="{cx + dx - 4:.1f},{base:.1f} {cx + dx + 4:.1f},{base:.1f} '
                f'{cx + dx + 2:.1f},{base + 16:.1f} {cx + dx - 2:.1f},{base + 16:.1f}" fill="#8d97a3"/>'
            )
        flame = base + 26.0
        parts.append(
            f'<polygon points="{cx - 14:.1f},{base + 16:.1f} {cx + 14:.1f},{base + 16:.1f} '
            f'{cx + 8:.1f},{flame:.1f} {cx - 8:.1f},{flame:.1f}" fill="#6a4a32" opacity="0.9"/>'
        )
        if shoes:
            shoe_y = base - 18
            parts.append(f'<rect x="{cx - 48}" y="{shoe_y:.1f}" width="16" height="16" fill="#c4a35a"/>')
            parts.append(f'<rect x="{cx + 32}" y="{shoe_y:.1f}" width="16" height="16" fill="#c4a35a"/>')
            if pushing:
                parts.append(
                    f'<line x1="{cx - 40}" y1="{shoe_y + 16:.1f}" x2="{cx - 40}" y2="{shoe_y - 28:.1f}" stroke="#2f6f4e" stroke-width="3"/>'
                )
                parts.append(
                    f'<polygon points="{cx - 40},{shoe_y - 34:.1f} {cx - 46},{shoe_y - 22:.1f} {cx - 34},{shoe_y - 22:.1f}" fill="#2f6f4e"/>'
                )
                parts.append(
                    f'<line x1="{cx + 40}" y1="{shoe_y + 16:.1f}" x2="{cx + 40}" y2="{shoe_y - 28:.1f}" stroke="#2f6f4e" stroke-width="3"/>'
                )
                parts.append(
                    f'<polygon points="{cx + 40},{shoe_y - 34:.1f} {cx + 34},{shoe_y - 22:.1f} {cx + 46},{shoe_y - 22:.1f}" fill="#2f6f4e"/>'
                )
        return "\n".join(parts)

    rail_top = y_of(STROKE_M)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="720" viewBox="0 0 1680 720">
  <rect width="1680" height="720" fill="#14181d"/>
  <text x="40" y="46" fill="#f4f1ea" font-family="Georgia, serif" font-size="28">Liftoff, same engines</text>
  <text x="1640" y="46" text-anchor="end" fill="#c4a35a" font-family="sans-serif" font-size="22">{clock}</text>
  <text x="280" y="96" text-anchor="middle" fill="#9aa3ad" font-family="sans-serif" font-size="16">Engines only</text>
  <text x="840" y="96" text-anchor="middle" fill="#8fd0ad" font-family="sans-serif" font-size="16">Ring, tanks full</text>
  <text x="1400" y="96" text-anchor="middle" fill="#c4a35a" font-family="sans-serif" font-size="16">Ring, {offload_t:.1f} t left behind</text>
  <clipPath id="sky"><rect x="0" y="110" width="1680" height="530"/></clipPath>
  <g clip-path="url(#sky)">
  <rect x="40" y="{pad:.1f}" width="480" height="16" fill="#3a414a"/>
  <rect x="600" y="{pad:.1f}" width="480" height="16" fill="#3a414a"/>
  <rect x="1160" y="{pad:.1f}" width="480" height="16" fill="#3a414a"/>
  <line x1="1124" y1="{rail_top:.1f}" x2="1140" y2="{rail_top:.1f}" stroke="#c4a35a" stroke-width="2"/>
  <line x1="1132" y1="{rail_top:.1f}" x2="1132" y2="{pad:.1f}" stroke="#c4a35a" stroke-width="2"/>
  {booster(280, h0, False, False)}
  {booster(840, h1, True, h1 < STROKE_M)}
  {booster(1400, h2, True, h2 < STROKE_M)}
  </g>
  <text x="1116" y="{max(rail_top - 8, 124):.1f}" text-anchor="end" fill="#c4a35a" font-family="sans-serif" font-size="13">40 m</text>
  <text x="280" y="690" text-anchor="middle" fill="#d5dbe3" font-family="sans-serif" font-size="15">{h0:.1f} m    {v0:.1f} m/s</text>
  <text x="840" y="690" text-anchor="middle" fill="#d5dbe3" font-family="sans-serif" font-size="15">{h1:.1f} m    {v1:.1f} m/s</text>
  <text x="1400" y="690" text-anchor="middle" fill="#d5dbe3" font-family="sans-serif" font-size="15">{h2:.1f} m    {v2:.1f} m/s</text>
  <text x="840" y="668" text-anchor="middle" fill="#9aa3ad" font-family="sans-serif" font-size="14">{"ring pushing" if engaged else "shoes have run off"}</text>
</svg>
'''


def _frame_lead(t: float, h0: float, h1: float, h2: float, v0: float, v1: float, v2: float, offload_t: float) -> str:
    """Park the unassisted rocket. The gap is a clock lead on the same flight."""
    lead_scale = 340.0 / 1300.0
    base_y = 520.0
    y1 = base_y - (h1 - h0) * lead_scale
    y2 = base_y - (h2 - h0) * lead_scale

    def ship(cx: float, top: float) -> str:
        return (
            f'<rect x="{cx - 22}" y="{top:.1f}" width="44" height="70" rx="3" '
            f'fill="#c5ced8" stroke="#1f4e79" stroke-width="2"/>'
            f'<polygon points="{cx - 10:.1f},{top + 70:.1f} {cx + 10:.1f},{top + 70:.1f} '
            f'{cx + 6:.1f},{top + 86:.1f} {cx - 6:.1f},{top + 86:.1f}" fill="#8d97a3"/>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="720" viewBox="0 0 1680 720">
  <rect width="1680" height="720" fill="#14181d"/>
  <text x="40" y="46" fill="#f4f1ea" font-family="Georgia, serif" font-size="28">Same flight, 0.6 s early</text>
  <text x="1640" y="46" text-anchor="end" fill="#c4a35a" font-family="sans-serif" font-size="22">{t:.0f} s</text>
  <text x="280" y="96" text-anchor="middle" fill="#9aa3ad" font-family="sans-serif" font-size="16">Engines only</text>
  <text x="840" y="96" text-anchor="middle" fill="#8fd0ad" font-family="sans-serif" font-size="16">Ring, tanks full</text>
  <text x="1400" y="96" text-anchor="middle" fill="#c4a35a" font-family="sans-serif" font-size="16">Ring, {offload_t:.1f} t left behind</text>
  <line x1="80" y1="{base_y + 90:.1f}" x2="1600" y2="{base_y + 90:.1f}" stroke="#3a414a" stroke-width="2"/>
  <clipPath id="sky"><rect x="0" y="108" width="1680" height="500"/></clipPath>
  <text x="840" y="652" text-anchor="middle" fill="#9aa3ad" font-family="sans-serif" font-size="14">The height gap is climb still left in that 0.6 s. Cutoff altitudes match.</text>
  <g clip-path="url(#sky)">
  {ship(280, base_y)}
  {ship(840, y1)}
  {ship(1400, y2)}
  </g>
  <text x="280" y="700" text-anchor="middle" fill="#d5dbe3" font-family="sans-serif" font-size="15">{h0/1000:.1f} km    {v0:.0f} m/s</text>
  <text x="840" y="700" text-anchor="middle" fill="#d5dbe3" font-family="sans-serif" font-size="15">+{h1 - h0:.0f} m    {v1:.0f} m/s</text>
  <text x="1400" y="700" text-anchor="middle" fill="#c4a35a" font-family="sans-serif" font-size="15">0.6 s early    +{h2 - h0:.0f} m</text>
</svg>
'''


def render(tmp: Path | None = None) -> Path:
    plain, full, light, offload, n = _traces()
    # Same burn, sampled coarsely, so the clock lead can be seen as altitude.
    gate = 130_000.0
    plain_long = simulate(0.0, 0.0, 0.0, gate_m=gate, sample_s=2.0)
    full_long = simulate(ASSIST_N, STROKE_M, 0.0, gate_m=gate, sample_s=2.0)
    light_long = simulate(ASSIST_N, STROKE_M, offload, gate_m=gate, sample_s=2.0)
    work = tmp or Path("/tmp/em-ascent-assist-frames")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    index = 0
    for i in range(n):
        (work / f"frame_{index:04d}.svg").write_text(_frame(i, plain, full, light, offload))
        index += 1
    hold = _frame(n - 1, plain, full, light, offload)
    for _ in range(8):
        (work / f"frame_{index:04d}.svg").write_text(hold)
        index += 1
    nt = min(len(plain_long["trace"]["t"]), len(full_long["trace"]["t"]), len(light_long["trace"]["t"]))
    for i in range(nt):
        t = float(plain_long["trace"]["t"][i])
        if t < 8.0:
            continue
        svg = _frame_lead(
            t,
            float(plain_long["trace"]["h"][i]),
            float(full_long["trace"]["h"][i]),
            float(light_long["trace"]["h"][i]),
            float(plain_long["trace"]["v"][i]),
            float(full_long["trace"]["v"][i]),
            float(light_long["trace"]["v"][i]),
            offload / 1000.0,
        )
        for _ in range(2):
            (work / f"frame_{index:04d}.svg").write_text(svg)
            index += 1
        last_lead = svg
    for _ in range(18):
        (work / f"frame_{index:04d}.svg").write_text(last_lead)
        index += 1
    png = work / "png"
    png.mkdir()
    # Rasterize the vector frames. Independent files, so parallel convert.
    workers = max(1, (os.cpu_count() or 2) - 2)
    subprocess.run(
        [
            "bash",
            "-lc",
            "printf '%s\\n' frame_*.svg | xargs -P "
            + str(workers)
            + " -I{} rsvg-convert -w 1280 {} -o png/{}.png",
        ],
        cwd=work,
        check=True,
    )
    gif = FIG / "launch-compare.gif"
    mp4 = FIG / "launch-compare.mp4"
    FIG.mkdir(parents=True, exist_ok=True)
    palette = work / "palette.png"
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(png / "frame_%04d.svg.png"),
            "-vf", "fps=12,scale=960:-1:flags=lanczos,palettegen",
            str(palette),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(png / "frame_%04d.svg.png"),
            "-i", str(palette),
            "-lavfi", "fps=12,scale=960:-1:flags=lanczos[x];[x][1:v]paletteuse",
            "-loop", "0", str(gif),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(png / "frame_%04d.svg.png"),
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(mp4),
        ],
        check=True,
        capture_output=True,
    )
    return gif


if __name__ == "__main__":
    print(render())
