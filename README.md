# em-ascent

Electromagnetic launch tube for a small rocket. The tube does the hard start. The motor takes over already climbing, so the motor can be small.

The reference craft is 1.50 kg wet, 70 mm diameter. The bore pitches it from 8° to 65° in the first 1.8 m, then runs straight. It leaves at 110 m/s, 42 m up. A 51 N motor then flies it. The same motor, launched from a 2 m pad rail, does not get there.

## Length and curvature

Peak axial load and tube length are the same decision. For this 110 m/s, 65° exit:

| Barrel load | Tube length | Muzzle height | Peak electrical power |
| --- | ---: | ---: | ---: |
| 10 g | 64.8 m | 58.1 m | 88 kW |
| 14 g | 47.3 m | 42.3 m | 119 kW |
| 18 g | 37.6 m | 33.5 m | 150 kW |
| 28 g | 25.5 m | 22.5 m | 226 kW |
| 50 g | 15.9 m | 13.8 m | 385 kW |
| 70 g | 12.4 m | 10.6 m | 521 kW |

Stored electrical energy stays near 49 kJ across that table, at 20% coil efficiency. A longer tube lowers the peak power and the peak g. It does not save much energy. The kinetic energy is set by the exit speed.

The reference pick is the 14 g row. It is the mildest barrel that still finishes inside 50 m. Fourteen g for about one second is a hard push for a small airframe, and it is less than the 19 g burnout load of the high-thrust pad motor below.

Curvature belongs at the breech, while the craft is still slow. The reference turn is a clothoid into a 1.5 m radius arc and a clothoid back to straight. Turn acceleration is 3 g. Peak side load is 6.0 g, at about 10 m/s. Side load on a circular turn run at constant acceleration from rest is `2 * a * Δθ`, so the radius does not set that ratio. A bigger radius spends more tube and finishes the turn faster, which is worse for the balls. A waterslide that keeps curving out to the muzzle would put the side load on the fast end. At 110 m/s the same 57° turn needs a radius of tens of meters or the balls get crushed.

![Tube length against barrel load](docs/figures/length_vs_g.png)

![Reference shot, speed and load](docs/figures/reference_shot.png)

## Ball transfers

The coils push the craft. The balls only keep the sleeve off the wall.

Put the balls in the tube, pointing inward, as ball transfers. A spring plunger with a fixed ball tip would skid. The ball has to be free to spin. Use silicon nitride. A steel ball in the coil bore becomes part of the magnet.

The reference liner is rings of 8 balls on a 120 mm pitch. The sleeve is 300 mm long, so nine balls on the outer wall share the turn load. Peak load is 17 N per ball. The spring rate that reaches that load at 0.8 mm of travel is 21 kN/m. Preload is 6 N.

The craft carries short rub pads, 25 mm long. A straight 300 mm sleeve in a 1.5 m radius bore would rise 7.5 mm off the wall at mid-span and jam. A 25 mm pad rises 0.05 mm, inside the spring travel.

Hertz pressure at 17 N on an 8 mm ball:

| Rub surface | Peak pressure |
| --- | ---: |
| Hard nonmagnetic race | 1.53 GPa |
| Aluminum | 0.93 GPa |
| PEEK | 0.15 GPa |

Aluminum is at the edge of brinelling, so the pressure case should not be the running surface. PEEK is soft enough to live, and it will wear. A hard nonmagnetic strip is the reusable answer. The straight barrel is the easy part for the balls: at 65° the wall only holds a component of the weight, about 6 N total, while the coils take the 220 N axial load.

## What the motor still has to do

Same craft. Isp 205 s. Cd 0.50. The gentle motor is T/W 3.5 at ignition, 51 N. The pad cases ride a 2 m rail at 65° so a slow gravity turn does not immediately bend them into the ground. The tube craft lights 0.45 m after the muzzle.

| Mission | Thrust | Peak motor load | Apogee on 0.40 kg | Propellant for a 1 km apogee | Peak dynamic pressure |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tube, then the gentle motor | 51 N | 4.8 g | 2389 m | 0.093 kg | 22 kPa |
| Pad rail, same gentle motor | 51 N | 4.7 g | 584 m | 3.13 kg | 25 kPa |
| Pad rail, high-thrust motor | 206 N | 19 g | 1826 m | 0.18 kg | 79 kPa |

The tube motor sees about 5 g. The high-thrust pad motor sees 19 g, four times the thrust, and a harsher max-q. The gentle motor on a pad can climb, and it needs about 3.1 kg of propellant to reach the same 1 km the tube reaches with 0.09 kg.

![Ascent comparison](docs/figures/ascent.png)

## What is modeled

The tube integration commands the craft acceleration and solves the axial force the coils have to supply, including gravity, rolling friction, and a 5% residual radial coil load. Work along the bore matches kinetic energy, potential energy, and friction work. That check is in `tests/test_tube.py`.

Coil shape, current, timing, and suck-back are not modeled. `data/reference_tube_profile.csv` is the force the coils have to produce. Capacitor mass is not in the craft mass. The motor is a point mass with constant thrust along the velocity vector after the rail or the muzzle.

The geometry map is 11,200 independent shots. On this machine that ran in 5.0 s on 86 processes. The V100 was left idle. Each shot is a short sequential integration, and the GPU was already busy with other work.

## Run

```bash
PYTHONPATH=src python -m pytest
PYTHONPATH=src python -m em_ascent.sweep
PYTHONPATH=src python -m em_ascent.report
```

`sweep` rewrites `data/geometry_map.csv` and `data/reference_choice.json`. `report` rewrites the profile, the flight table, and the figures.

## License

MIT. Copyright 2026 Nicholas Dean Perry.
