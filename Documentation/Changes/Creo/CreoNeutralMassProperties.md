# Creo neutral mass properties

## Change

Extends `src/convert/adapters/creo/VisibGeom.py` to decode positional `local_sys` origin slots and
compute a convex-polyhedron volume and centre of mass from the proven closed shell. The neutral
`DesignBody` now carries volume, vertex count, and bounding box.

## Behaviour

`DecodeLocalSystem` decodes up to twelve slots with the exact compact lane:

```text
0x0f = 1.0   0x18 = 0.0   0x10 = -1.0   0xe4..0xe6 = repeat 1/2/3
```

The first nine slots are the rotation columns `u`, `v`, `normal`; the last three are the plane
origin. Definition-site bodies carry an `f9 04 03` header; replayed prototypes start directly with
the slots.

`ReadMassProperties` treats each plane as a half-space `normal · p <= normal · origin`, orients each
normal outward using the average plane origin, intersects every triple of non-parallel planes,
keeps points inside all half-spaces, orders the points on each plane around its normal, and sums
signed tetrahedra with the origin. The result is the absolute volume and the volume-weighted
centroid.

The body receives `volume`, `vertex_count`, and `bounding_box`. Metadata reports `creo.volume` and
`creo.centroid`.

## Verification

Retained ladder control through the production adapter:

```text
body solid=1 vertices=8 volume=18482541.490319017 valid=True
meta creo.volume=18482541.490319017
     creo.centroid=(15.038745265314674, -135.165, 14.792732911858081)
```

The ladder is an axis-aligned box with decoded plane frames:

```text
77  u=(1,0,0) v=(0,0,-1) n=(0,1,0)  origin=(0, 0, 0)
82  u=(1,0,0) v=(0,0,-1) n=(0,1,0)  origin=(0, -270.33, 0)
87  u=(0,0,-1) v=(0,1,0) n=(1,0,0)  origin=(-154.4303300690026, 0, -86.06680966899467)
89  u=(-1,0,0) v=(0,1,0) n=(0,0,-1) origin=(-154.4303300690026, 0, 115.65227549271083)
91  u=(0,0,1) v=(0,1,0) n=(-1,0,0)  origin=(184.50782059963194, 0, 115.65227549271083)
93  u=(1,0,0) v=(0,1,0) n=(0,0,1)   origin=(184.50782059963194, 0, -86.06680966899467)
```

Analytic cross-check:

```text
dx = 184.50782059963194 - (-154.4303300690026)  = 338.93815066863454
dy = 0 - (-270.33)                              = 270.33
dz = 115.65227549271083 - (-86.06680966899467)  = 201.7190851617055
V  = dx * dy * dz                               = 18482541.490319017
C  = (dx/2 offset, -135.165, 14.792732911858081)
```

The computed volume and centroid match the analytic box exactly.

The empty control has no geometry, so `volume=None`, `creo.centroid=None`.

`TestFeatureRows` asserts the synthetic single-plane case stays open: `volume=None`,
`vertex_count=0`, `creo.volume=None`, `creo.centroid=None`.

## Limits

- The volume is computed from identifier-proven plane frames, not from Creo's own mass properties.
- Only convex polyhedra are handled. Concave shells, holes, and surfaces need trimming.
- Face edge endpoints are still not used; curved edges are approximated by their plane carriers.
- `creo.geometry_decoded` is true only when shell closure is proven.
- The writer is unchanged and still performs exact source replay only.
- `vendor_loadable` and `application_usable` remain false.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Shell closure change entry](CreoNeutralShellClosure.md)
- [Surface change entry](CreoNeutralSurfaceRecords.md)
