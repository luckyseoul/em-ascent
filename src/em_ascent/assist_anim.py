"""Side-by-side vector frames of the first seconds, engines only versus the pusher."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from em_ascent.starship_assist import simulate

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "docs" / "figures"
STROKE_M = 40.0
ASSIST_N = 5.0e6
DURATION_S = 5.0
FPS = 12
VIEW_M = 90.0


def _traces():
    plain = simulate(0.0, 0.0, 0.0, gate_m=VIEW_M + 5.0, sample_s=1.0 / FPS)
    pushed = simulate(ASSIST_N, STROKE_M, 0.0, gate_m=VIEW_M + 5.0, sample_s=1.0 / FPS)
    n = min(len(plain["trace"]["t"]), len(pushed["trace"]["t"]))
    n = min(n, int(DURATION_S * FPS) + 1)
    return plain["trace"], pushed["trace"], n


def _frame(i: int, n: int, plain: dict, pushed: dict) -> str:
    t = float(plain["t"][i])
    h0 = float(plain["h"][i])
    h1 = float(pushed["h"][i])
    v0 = float(plain["v"][i])
    v1 = float(pushed["v"][i])
    # Pad at y=640. 70 m of air maps to 520 px.
    scale = 500.0 / VIEW_M
    ground = 620.0
    pad = ground + 22.0

    def y_of(height: float) -> float:
        return ground - height * scale

    engaged = h1 < STROKE_M
    ahead = h1 - h0
    clock = f"{t:0.2f} s"

    def booster(cx: float, height: float, shoes: bool) -> str:
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
            if engaged:
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
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#14181d"/>
  <text x="40" y="46" fill="#f4f1ea" font-family="Georgia, serif" font-size="28">Liftoff, same engines</text>
  <text x="1180" y="46" text-anchor="end" fill="#c4a35a" font-family="sans-serif" font-size="22">{clock}</text>
  <text x="320" y="96" text-anchor="middle" fill="#9aa3ad" font-family="sans-serif" font-size="18">Engines only</text>
  <text x="960" y="96" text-anchor="middle" fill="#8fd0ad" font-family="sans-serif" font-size="18">Engines plus 5 MN ring</text>
  <clipPath id="sky"><rect x="0" y="110" width="1280" height="530"/></clipPath>
  <g clip-path="url(#sky)">
  <rect x="70" y="{pad:.1f}" width="500" height="16" fill="#3a414a"/>
  <rect x="710" y="{pad:.1f}" width="500" height="16" fill="#3a414a"/>
  <line x1="690" y1="{rail_top:.1f}" x2="706" y2="{rail_top:.1f}" stroke="#c4a35a" stroke-width="2"/>
  <line x1="698" y1="{rail_top:.1f}" x2="698" y2="{pad:.1f}" stroke="#c4a35a" stroke-width="2"/>
  {booster(320, h0, False)}
  {booster(960, h1, True)}
  </g>
  <text x="688" y="{max(rail_top - 8, 124):.1f}" text-anchor="end" fill="#c4a35a" font-family="sans-serif" font-size="13">40 m</text>
  <text x="320" y="680" text-anchor="middle" fill="#d5dbe3" font-family="sans-serif" font-size="16">{h0:.1f} m    {v0:.1f} m/s</text>
  <text x="960" y="680" text-anchor="middle" fill="#d5dbe3" font-family="sans-serif" font-size="16">{h1:.1f} m    {v1:.1f} m/s</text>
  <text x="640" y="680" text-anchor="middle" fill="#c4a35a" font-family="sans-serif" font-size="16">ahead {ahead:.1f} m</text>
  <text x="640" y="132" text-anchor="middle" fill="#9aa3ad" font-family="sans-serif" font-size="14">{"ring pushing" if engaged else "shoes have left the motors"}</text>
</svg>
'''


def render(tmp: Path | None = None) -> Path:
    plain, pushed, n = _traces()
    work = tmp or Path("/tmp/em-ascent-assist-frames")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    for i in range(n):
        (work / f"frame_{i:04d}.svg").write_text(_frame(i, n, plain, pushed))
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
            + " -I{} rsvg-convert -w 960 {} -o png/{}.png",
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
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(mp4),
        ],
        check=True,
        capture_output=True,
    )
    return gif


if __name__ == "__main__":
    print(render())
