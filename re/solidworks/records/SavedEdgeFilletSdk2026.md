# Saved constant radius edge fillet readback

Workstream `B04-SW2026-EDGE-FILLET-SOURCES`, PR #121. The scoped SDK
reader builds on the checked [linked archive](EdgeFilletArchive2026.md)
and [retained rollback](EdgeFilletRollback2026.md) from SOLIDWORKS 2026
SP05.2 `34.5.2.0604`. The separate partition-omission
[trial](../measurements/2026/EdgeFilletColdDiagnosticResult01.json) verifies
the native recomputation path on one saved history.

The ordinary version-19000 Default configuration path binds the selected
edge, radial item and keeper through their one shared reference. Its four
native face keys reach the same stock creation event in both headers and
join to the preceding partition state. The first two faces meet the actual
edge. The last two each own one endpoint. The historical file handle and
both headers agree on the document name, path and configuration. The
originals use an empty historical path in all three owners. The edited
saves retain the same original file locator.

The active and previous native body slot, atom and feature dependency match
the checked transaction. The actual prior box, convex edge, six planar
carriers, cylindrical carrier and tangent vertices constrain the recovered
body. The SDK binds the B-rep to the live design body and preserves the
kernel's positive or negative circle sense when deriving the cap trims.
Every accepted span is a quarter turn. The same live radius parameter
owns the fillet definition and its editable D1, and the selection retains
its actual preceding-edge midpoint, endpoints and archive provenance.
The body summary derives volume, area and signed centroid from the verified
box and quarter round.

The [guarded receipt](../measurements/2026/SdkSavedEdgeFilletRead01.json)
covers four exact disclosed original and edited archives. All have one
solid with 7 faces, 15 edges and 10 vertices. Twenty volume, surface area
and signed centre comparisons match the corresponding native observations
to six significant figures. The four selected-edge slots are 227, 226,
228 and 227. Separate wrong radius aliases, crossed support identities,
circle sense and unrelated decoded geometry refuse the typed qualification.
No runtime data access occurs in the guarded readers. History-only and
raw extraction retain their ordinary routing.

```sh
python3.14 -I -B re/tooling/sw2026/edge_fillet_source/CheckSavedFillet.py \
  --capture /path/to/disclosed/EdgeFilletSource03/Capture
```

Generative fillet edge stamps, result keepers and physical
`fc20` initialization remain unresolved construction requirements. The
native partition-omission result does not remove those owners from the
saved files. The protected pre-writer lock stays sealed.
