# Starship electromagnetic launch assist

A retrofit on the Starbase mount. The bore, or in this case a short pusher, supplies the first few meters per second. Super Heavy still does the ascent. The point is methalox left in the farm tanks, not a gun that replaces the rocket.

Starship's tank wall is 304L stainless, which will not serve as an armature. The shoes are bolted on. The chopsticks stay a catching tool. They are built for a nearly empty booster, not a 5,300 t liftoff.

## Vehicle and pad

Block 3 public figures. Where two numbers are in circulation, both are listed.

| Item | Figure |
| --- | --- |
| Stack | 124.4 m, 9 m diameter, about 5,000 to 5,300 t fully fueled |
| Super Heavy | 72.3 m, about 3,650 t propellant |
| Propellant split | about 2,860 t liquid oxygen, 790 t liquid methane, mixture ratio about 3.6 |
| Booster engines | 33 Raptor 3, liftoff thrust 80.8 MN |
| Liftoff thrust-to-weight | about 1.55 |
| Ship | about 52 m, about 1,600 t propellant, 3 sea-level and 3 vacuum Raptors |
| Raptor 3, flight rating | 250 tf sea level, about 275 tf vacuum |
| Raptor 3, stand post (Aug 2024) | 280 tf, 1,525 kg, 350 bar, 350 s |
| Chamber pressure | up to 330 bar in operation, 350 bar design |
| Cycle | full-flow staged combustion, methane and oxygen, subcooled |
| Tower | about 146 m, chopsticks at the grid-fin catch pins |
| Mount | orbital launch mount over a water-cooled steel plate, hold-down clamps, no flame trench |

Booster dry mass of 275 t is the published Block 1 number. Block 3 dry mass is not published.

## Simulated liftoff

The engines are at 80.8 MN before the clamps let go. The pusher adds force on top of that, straight up, until the shoes run off the end of the stroke. Pitch follows altitude, the same schedule with and without the pusher, so the turn is not doing the work. The comparison is booster burnout speed. Propellant left in the tanks is the largest offload that still matches the unassisted burnout speed.

The reference ring is 5 MN and 40 m. The shoes let go at 3.5 s. The stack is then at 23 m/s, and most of that speed is the Raptors. The push delivers 17.6 MN·s and 200 MJ. Mechanical power at the shoes peaks at 115 MW, which is the force times the speed at release. The stroke lasts 3.5 s. Electrical power is higher than 115 MW by whatever the motors lose.

Leave 14.9 t in the farm and the booster burnout speed matches the unassisted flight: 11.7 t of oxygen and 3.2 t of methane. That 14.9 t is 0.59 s of booster burn at the sea-level flow of 25.2 t/s. The lighter stack flies the same trajectory 0.6 s early. Speed at a given altitude matches. At the lighter stack's own cutoff it is 8 m higher. A frame near 144 s can show it 1.3 km up on the other two, because the baseline still has 0.6 s of climb left, at about 2.2 km/s.

Full tanks, with the same shove and no propellant removed, are a few meters per second faster at cutoff. That leftover changes when the pitch program changes. The offload does not: a pitch stop at 45° leaves 14.6 t, and a stop at 80° leaves 15.2 t. Quote the tonnes.

This stack is booked as 5,300 t, with 3,650 t in the booster and 1,600 t in the ship. That leaves 50 t for both dry masses and the payload, so the books do not close, and cutoff in the model is 2,630 m/s at 111 km. The offload follows liftoff thrust-to-weight. The same ring on a 5,625 t stack leaves 18.1 t, and on a 5,725 t stack leaves 19.2 t. Thirty-three engines at the 280 tf stand rating, on the 5,300 t stack, leave 11.1 t. Carry 14.9 t as the 5,300 t, 80.8 MN case, inside a range of about 11 to 19 t.

Left is engines only. Middle is the ring with the tanks still full. Right is the ring with the 14.9 t left in the farm. The opening is the stroke. The second half draws the clock lead as altitude, and the caption says the cutoff altitudes match.

![Liftoff with and without the ring](docs/figures/launch-compare.gif)

![Simulated propellant left in the tanks](docs/figures/sim-fuel.png)

| Force | 20 m stroke | 40 m stroke | 60 m stroke | 100 m stroke |
| --- | ---: | ---: | ---: | ---: |
| 2.5 MN | 5.6 t | 7.8 t | 9.5 t | 12.1 t |
| 5 MN | 10.6 t | 14.9 t | 18.1 t | 23.1 t |
| 8 MN | 16.3 t | 22.8 t | 27.7 t | 35.2 t |
| 10 MN | 19.8 t | 27.7 t | 33.6 t | 42.7 t |
| 15 MN | 27.9 t | 38.9 t | 47.2 t | 59.9 t |

Fifteen meganewtons is six Raptors at the 250 tf flight rating. Split across two shoes, that is three Raptors on a fitting. That row is the edge of what the skirt can even be asked to do. The 5 MN ring is the case that fits the mount.

The grid is one formula. Propellant left behind is about the push impulse times the propellant flow, divided by thrust minus weight. Thrust minus weight is 28.8 MN, so 36% of the thrust is accelerating the stack, and an outside push is worth about 2.8 times the rocket-equation credit for the same impulse. The formula sits within about 5% of every cell above. For the reference ring it gives 15.4 t against the integrated 14.9 t. Counted as a pure delta-v, that impulse is only 3.3 m/s and the rocket equation returns 5.5 t.

A speed that is actually present at liftoff is worth more than the ring, because the ring never adds more than those 3.3 m/s. The integration, given that speed as an initial condition and then flown to the same burnout, leaves the following propellant in the farm. The rocket-equation column is the 2.8-times-smaller credit.

![Propellant a real liftoff speed is worth](docs/figures/fuel-save.png)

| Speed at liftoff | This integration | Rocket equation |
| --- | ---: | ---: |
| 10 m/s | 45 t | 17 t |
| 20 m/s | 88 t | 33 t |
| 50 m/s | 205 t | 82 t |
| 100 m/s | 373 t | 163 t |

About 78 percent of that is oxygen and 22 percent is methane. The 50 and 100 m/s rows need a new track. The stroke on this pad is tens of meters, and the skirt cannot take a local load comparable to the whole engine bay.

## Three retrofits

**Pusher ring.** A truss on the existing mount foundation. Linear motors push bolted shoes on the aft skirt for 40 m, then the shoes run off. Engines are already at full thrust. Five meganewtons. The integration leaves 14.9 t of methalox in the tanks at the same booster burnout speed. The shoes deliver 200 MJ, and mechanical power peaks at 115 MW as they let go.

The bells climb into the ring. After the first moments the steel is in the plume, so "the flame stays on the plate" describes liftoff, not the rest of the stroke. The hold-down clamps already react about 29 MN at release, 80.8 MN of thrust against 52 MN of weight. Five meganewtons at those hardpoints is a familiar load, pushed up.

![Pusher ring mockup](docs/figures/mockup-pusher.png)

**Hold-down stroke.** The clamps already carry the fueled stack. Give them about 10 m of powered travel. At 5 MN that leaves 7.6 t in the tanks. The plume also spends less time on the deluge plate.

![Hold-down mockup](docs/figures/mockup-holddown.png)

**Tower-column rail.** A second pin set lower on the booster, in a rail lagged to the tower columns. The grid-fin pins are too high. Little tower remains above them. The column load is the same few-meganewton class as the ring. Use this only if the mount foundation cannot take the ring.

![Tower rail mockup](docs/figures/mockup-tower.png)

Electricity is a capacitor yard beside the pad. Starbase already runs an air separation plant. The structure is the constraint, not the energy.

## Out of scope

A ground track to hundreds of meters per second. The fuel save is real there, and the stroke at a force this vehicle can take is a new facility.

Redraw the figures with `python src/figures.py`.

## License

MIT. Copyright 2026 Nicholas Dean Perry.
