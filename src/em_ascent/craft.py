"""Reference small craft. One vehicle for the geometry map and the ascent comparison."""

from em_ascent.bearings import BallLiner

# 1.50 kg wet on the tube. The sleeve stays with the craft.
WET_KG = 1.50
DRY_KG = 1.10
PROP_KG = 0.40
ISP_S = 205.0
DIAMETER_M = 0.070
CD = 0.50

# Coil bus to axial mechanical work. Multistage coilguns are often worse than this.
ETA_COIL = 0.20

# Gentle motor the tube is meant to allow, and a pad solid that has to start itself.
TW_GENTLE = 3.5
TW_PAD = 14.0

# Breech loader angle. The turn pitches up from here.
GAMMA0_DEG = 8.0

# Older fixed offset. The light plan in ignition.py is the muzzle clearance to use.

LINER = BallLiner()
