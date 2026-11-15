# Creo neutral surface prototypes

## Change

Adds `src/convert/adapters/creo/VisibGeom.py` and extends the Creo reader to decode `VisibGeom`
plane and curve prototypes into a neutral `DesignBody` with face and edge counts and per-face
records.

## Behaviour

`ReadGeometry` parses the `VisibGeom` tagged stream and collects:

- plane prototypes (`geom_id`, `geom_type` 34, `feat_id`, `envlp`, `outline`, `local_sys`);
- curve prototypes (`crv_id`, `type`, `feat_id`, `crv_pnt_arr`).

Per-element schema resets are applied at the array boundaries: a bare `e3`, a compact identifier,
one byte, and the element `feat_id` byte. A `0x22` second byte selects the surface schema start,
anything else selects the curve schema start. This recovers every declared element:

```text
srf_array 6  -> 77, 82, 87, 89, 91, 93
crv_array 12 -> 78, 79, 80, 81, 83, 84, 85, 86, 88, 90, 92, 94
```

The reader then emits one `DesignBody` when surfaces and at least one feature exist:

```text
id              creo:body:1
name            Creo surface body
final_feature_id last decoded feature
topology        TopologyCounts(face_count=surfaces, edge_count=curves)
attributes      creo.faces, creo.curves, creo.surface_count, creo.curve_count
```

Each face attribute carries `id`, `geom_type`, `feature_id`, `envelope`, `outline`, and
`local_system`. Each curve attribute carries `id`, `curve_type`, `feature_id`, and `points`.
The body also carries `creo.logical_objects`, the decoded `lo_id`/`next_lo_ptr` chain with each
object's `lo_type`, `lo_subtype`, and `feat_id`.

Metadata reports `creo.surface_count`, `creo.curve_count`, and
`creo.surface_prototypes_decoded`. `creo.geometry_decoded` remains false because surface closure
and shell topology are not established.

## Limits

- Prototype records only: no shared-edge topology, loop orientation, or shell closure, so the body
  is a surface grouping and not a proven solid.
- The logical-object chain decodes (ladder: `95 -> 96 -> 97 -> 98 -> 99 -> 100 -> 0`), with two
  classes: three objects of type 700 (subtypes 751, 750, 752) and three of type 701 (755, 754,
  759), all owned by feature 74. The edge records that would join them into shells still arrive
  partly as compound nodes (`closed`, `end_id`), so closure cannot be proven.
- `solid_count`, `shell_count`, and `vertex_count` stay zero.
- Sketch entities and B-rep shells are not decoded.
- The writer is unchanged and still performs exact source replay only.

## Verification

Read through the production adapter on the retained ladder control:

```text
bodies [('creo:body:1', 'Creo surface body', 6, 12, 'creo:feature:74')]
meta   creo.surface_count=6 creo.curve_count=12 creo.logical_object_count=6
       creo.surface_prototypes_decoded=True creo.geometry_decoded=False
logical_objects 95->96->97->98->99->100->0
```

`TestFeatureRows` also asserts the synthetic path: one `VisibGeom` plane yields
`creo:body:1` with `face_count=1`, `edge_count=0`, `final_feature_id='creo:feature:5'`, and
face `creo:face:77` with `geom_type=34`, `feature_id=74`, and envelope `(1.0, 1.0, 1.0, 1.0)`.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Dimension change entry](CreoNeutralDimensionRecords.md)
- [Compound-boundary gotcha](../../Gotchas/Conversion/CreoTaggedCompoundBoundary.md)
