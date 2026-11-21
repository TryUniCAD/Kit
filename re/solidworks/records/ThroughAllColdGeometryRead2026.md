# Cache-free circular through-all geometry

Task `B04-SW2026-EXTRUDE-THROUGHALL` shares the typed archive and analytic solid builders in PR #121. The source is the actual generated single mid-plane stock and circular cut on one resolved principal datum. The part contains an empty managed body state on this path.

The stock geometry occupies `[-depth/2, depth/2]` along its real sketch normal. A one-direction native cut starts at the sketch. The default reaches the negative stock cap. The reverse flag reaches the positive cap. A cut with two active through-all directions reaches both caps. The clipped geometry intervals are derived from the stock driver. The cut length and its parameter slots remain absent.

The analytic reader creates the stock's planar boundary and the circular cylinder. One inlet adds a reversed inner loop to the selected stock cap and retains the cylinder's closed inner end. Two inlets leave the complete cylindrical wall and remove both circular cap regions. The existing blind-pocket path uses its original finite interval and opening.

| Case | Measured scope | Faces | Edges | Vertices | Axial centre of mass |
| --- | --- | ---: | ---: | ---: | ---: |
| G01, Front | Exact native open/rebuild and independent analytic prediction | 8 | 14 | 10 | `-0.000136745801390 m` |
| G02, Top | Frozen independent analytic prediction | 8 | 14 | 10 | `0.000110886128773 m` |
| G03, Right | Frozen independent analytic prediction | 7 | 14 | 10 | `0 m` |

The first one-direction comparison matched volume and area while the axial centre of mass had the wrong sign. The verified native through-cut direction follows its operation's negative-normal default. This is consistent with the existing positive-normal blind cut reached by the reverse flag. The measured final reconstruction uses the actual cut direction and sketch frame.

The [audit](../../tooling/sw2026/AuditThroughAllColdGeometry.py) uses the exact generated files, their premeasurement predictions and the signed G01 oracle record. Six independent public reader processes produce the same closed B-reps from path and bytes. It calculates centre of mass from the reconstructed stock bounds and the world coordinates of the two circle centres. All three components, volume and area agree at relative tolerance `1e-10`, with absolute centre tolerance `1e-12 m`. The [receipt](../measurements/2026/ColdThroughAllGeometryRead01.json) binds all six reads to the source code and input hashes. The durable test checks the signed rim positions and closed geometry under all three end selections.
