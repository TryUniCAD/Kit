# SOLIDWORKS feature-definition evidence

The blind boss in the feature-ladder recovery corpus already has an extrusion
definition. The native-only findings in group G1 of
[PR #372](https://github.com/TryUniCAD/Kit/pull/372) refer to other timeline
records. This investigation does not change the reader or the receipt rules.

## Offline receipt replay

Strict native decode and neutral serialization replayed all 111 recovery parts.
The SOLIDWORKS total is unchanged at 8,547 unresolved entries; the committed
mixed-format total is 8,619, including 72 Fusion entries. Each row in the table
counts native-only definitions. Each definition also has a separate retained-byte
finding, for 2,775 native-only definitions and 2,775 byte findings in total.

| Native record | Before | After |
| --- | ---: | ---: |
| Principal planes | 333 | 333 |
| Origin | 111 | 111 |
| Sketch profile | 111 | 111 |
| Directional lights | 333 | 333 |
| Ambient light | 111 | 111 |
| Lights and Cameras | 111 | 111 |
| Exploded Views | 111 | 111 |
| Notes rows | 222 | 222 |
| Comments, Favorites, History, Selection Sets, Sensors, Design Binder, Annotations, Surface Bodies, Solid Bodies, Markups, Equations, SOLIDWORKS Materials (each) | 111 | 111 |

The resolved principal datum reader already has a typed geometry result. The
neutral reference-plane definition requires a parent plane and an offset, which
do not describe a built-in datum. The resolved folder reader checks the name,
identity and record boundary, but does not expose an owned child list. The
`OneLights.SLDPRT` and `TwoLights.SLDPRT` controls decode with one and two
directional timeline rows, respectively. This confirms row count, not ownership
or interpretation of the light payload. The exploded-view row does not establish
that an exploded state exists. Promoting these definitions needs neutral types
that can express the verified fields without losing their native records.

## Independent captures still needed

Keep the 111 direction/frame/operation findings unresolved. For a rectangular
blind boss, retain each native save and an independent API inventory, including
persistent feature and sketch identifiers, the API values below, and body
measurements. Use fresh saved captures for validation.

- **Direction:** Save a forward/reversed pair with identical sketch support and
  depth. Record the native reverse flag and the signed extrusion vector in model
  coordinates. Measure the body centroid to distinguish the two sides.
- **Frame:** Save the same asymmetric, offset rectangle on each principal plane.
  Hold depth and direction fixed. Record the sketch-to-model transform (origin
  and all three axes), transformed sketch points and the model-space centroid.
- **Operation:** Save a first boss, an overlapping boss with merge on and off,
  and a cut on an existing body. Record the native operation and merge setting,
  feature scope, and persistent input/output body identities. Measure body
  counts and volumes before and after to distinguish create, join and cut.
