import math

import pytest

from em_ascent.constants import G0
from em_ascent.orbit import ISP1_S, K1, STAGE1_DV_MPS, payload_for_liftoff, stack_for_payload


def test_stage_propellant_matches_the_rocket_equation():
    payload = 50.0
    # Upper stage removed: call the first-stage formula through a zero second stage by assist logic.
    stack = stack_for_payload(payload, assist_mps=0.0)
    ratio = math.exp(STAGE1_DV_MPS / (ISP1_S * G0))
    above = payload + stack.prop2_kg + stack.struct2_kg
    expect = above * (ratio - 1.0) / (1.0 + K1 - ratio * K1)
    assert stack.prop1_kg == pytest.approx(expect)


def test_assist_cuts_propellant_and_raises_payload():
    pad = stack_for_payload(10.0, 0.0)
    assisted = stack_for_payload(10.0, 400.0)
    assert assisted.propellant_kg < pad.propellant_kg
    assert payload_for_liftoff(pad.liftoff_kg, 400.0) > 10.0
