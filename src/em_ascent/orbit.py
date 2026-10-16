"""Two-stage orbit after an electromagnetic assist.

The bore subtracts from the first-stage delta-v. The rocket still flies the
rest of the way to a 200 km eastward orbit. Pad budget is 9200 m/s, which
already folds in gravity loss, drag, and Earth rotation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from em_ascent.constants import G0

# 200 km circular, eastward. Gravity, drag, and rotation are inside this number.
PAD_DV_MPS = 9200.0
STAGE1_DV_MPS = 5400.0
STAGE2_DV_MPS = 3800.0
ISP1_S = 282.0
ISP2_S = 330.0
# Stage hardware mass divided by that stage's propellant.
K1 = 0.10
K2 = 0.14


@dataclass(frozen=True)
class Stack:
    assist_mps: float
    payload_kg: float
    prop1_kg: float
    struct1_kg: float
    prop2_kg: float
    struct2_kg: float

    @property
    def propellant_kg(self) -> float:
        return self.prop1_kg + self.prop2_kg

    @property
    def liftoff_kg(self) -> float:
        return self.payload_kg + self.propellant_kg + self.struct1_kg + self.struct2_kg


def _stage_propellant(mass_above_kg: float, dv_mps: float, isp_s: float, k: float) -> tuple[float, float]:
    """Propellant and structure to give `mass_above_kg` a delta-v."""
    if dv_mps <= 0.0:
        return 0.0, 0.0
    ratio = math.exp(dv_mps / (isp_s * G0))
    denom = 1.0 + k - ratio * k
    if denom <= 0.0:
        raise ValueError("stage structure is too heavy for this delta-v")
    prop = mass_above_kg * (ratio - 1.0) / denom
    return prop, k * prop


def stack_for_payload(payload_kg: float, assist_mps: float = 0.0) -> Stack:
    dv1 = STAGE1_DV_MPS - assist_mps
    if dv1 < 0.0:
        dv1 = 0.0
    prop2, struct2 = _stage_propellant(payload_kg, STAGE2_DV_MPS, ISP2_S, K2)
    above = payload_kg + prop2 + struct2
    prop1, struct1 = _stage_propellant(above, dv1, ISP1_S, K1)
    return Stack(assist_mps, payload_kg, prop1, struct1, prop2, struct2)


def payload_for_liftoff(liftoff_kg: float, assist_mps: float = 0.0) -> float:
    """Supplies that fit inside a fixed liftoff mass."""
    lo, hi = 0.01, liftoff_kg
    best = 0.0
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        try:
            glow = stack_for_payload(mid, assist_mps).liftoff_kg
        except ValueError:
            hi = mid
            continue
        if glow <= liftoff_kg:
            best = mid
            lo = mid
        else:
            hi = mid
    return best
