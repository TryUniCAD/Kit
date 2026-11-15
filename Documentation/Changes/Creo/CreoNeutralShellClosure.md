# Creo neutral shell closure

## Change

Extends `src/convert/adapters/creo/VisibGeom.py` to decode the curve half-edge graph
(`crv_hdr_geom_ptr[0/1]`, `next_crv_hdr_ptr[0/1]`) and prove shell closure, setting real solid and
shell counts on the neutral body.

## Behaviour

Each curve carries two adjacent face identifiers and two next-curve identifiers, one per side. The
reader builds face loops by following `next_crv_hdr_ptr[slot]` from each edge assigned to a face and
requires the chain to return to its start. A solid is proven only when:

- every face loop closes;
- every edge has two face identifiers (no boundary edge);
- the face graph has at least one connected component.

Then `TopologyCounts` receives `solid_count`, `shell_count`, `face_count`, `edge_count`, and
`valid=True`. Metadata reports `creo.solid_count`, `creo.shell_count`, `creo.closed_loop_count`,
`creo.shell_closure_proven`, and `creo.geometry_decoded`.

## Verification

Retained ladder control through the production adapter:

```text
body creo:body:1 solid=1 shell=1 faces=6 edges=12 valid=True
meta creo.solid_count=1 creo.shell_count=1 creo.closed_loop_count=6
     creo.shell_closure_proven=True creo.geometry_decoded=True
```

The ladder is a rectangular extrusion. Its six faces are the two caps (`77`, `82`) and four sides
(`87`, `89`, `91`, `93`); the twelve edges form four-edge loops on each face:

```text
78 (77,87) next (79,88)   83 (82,87) next (86,90)   88 (87,93) next (83,81)
79 (77,89) next (80,90)   84 (82,89) next (83,92)   90 (89,87) next (84,78)
80 (77,91) next (81,92)   85 (82,91) next (84,94)   92 (91,89) next (85,79)
81 (77,93) next (78,94)   86 (82,93) next (85,88)   94 (93,91) next (86,80)
```

The empty control has no geometry, so `solid_count=0`, `shell_count=0`, and
`creo.geometry_decoded=False`.

`TestFeatureRows` asserts the synthetic single-plane case stays open: `solid_count=0`,
`shell_count=0`, `valid=False`, `creo.shell_closure_proven=False`.

## Limits

- Closure is proven from identifier connectivity, not from measured geometry. Volume and centre of
  mass are not computed.
- Curves are treated as edges without a carrier-geometry admission check.
- The writer is unchanged and still performs exact source replay only.
- `vendor_loadable` and `application_usable` remain false.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Surface change entry](CreoNeutralSurfaceRecords.md)
- [Compound-boundary gotcha](../../Gotchas/Conversion/CreoTaggedCompoundBoundary.md)
