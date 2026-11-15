# Creo neutral feature identity records

## Change

Adds `src/convert/adapters/creo/Records.py` and wires it into the Creo reader. The adapter now
decodes `AllFeatur` feature identity rows into neutral `FeatureStep` records instead of returning an
empty feature timeline.

## Behaviour

Feature rows are read by walking the decoded `first_feat_ptr`/`next_feat_ptr` chain and taking the
first `id` and `type` after each link. If no chain is present, the decoder falls back to the row
anchor: a row starts at offset zero or immediately after a `0xe3` byte and carries
`e3 f6 <compact-class> e1` within the next 16 bytes. The class must be a known feature class:

| Class | Label |
| ---: | --- |
| 911 | `hole` |
| 913 | `round` |
| 914 | `chamfer` |
| 916 | `cut` |
| 917 | `protrusion` |
| 923 | `datum_plane` |
| 926 | `section` |
| 927 | `draft` |
| 942 | `surface` |
| 946 | `surface_merge` |
| 979 | `coordinate_system` |

Rows shorter than 16 bytes are rejected in the anchor fallback, which drops the six-byte false
positives seen in the ladder control.

Each record carries:

```text
id          creo:feature:<feature-id>
name        Creo <class-label> <feature-id>
kind        FeatureKind.NATIVE
order       discovery order
provenance  ProvenanceSpan("AllFeatur", offset, length, "feature_row")
attributes  creo.feature_id, creo.root_class, creo.root_class_label
```

The reader also reports `creo.feature_rows_decoded`, `creo.feature_row_count`,
`creo.feature_history_decoded`, and `creo.geometry_decoded`. The last two stay false because no
parameters, sketches, dimensions, or geometry are decoded.

## Limits

- Identity and root class only. No parameter, sketch, dimension, or definition body.
- The chain walk covers every linked feature; the anchor fallback is used only when no chain is
  present.
- The production writer is unchanged and still performs exact source replay only.
- `vendor_loadable` and `application_usable` remain false.

## Verification

Retained controls through the production adapter:

```text
empty  feature_timeline: 7 datum_plane, 5 datum_plane, 3 datum_plane, 11 coordinate_system
ladder feature_timeline: 7 datum_plane, 5 datum_plane, 3 datum_plane, 11 coordinate_system,
                         67 datum_plane, 75 datum_plane, 74 protrusion
```

`TestFeatureRows` in `tests/convert/creo/CreoTests.py` builds a synthetic part with a real
`AllFeatur` section boundary and asserts:

- feature ids `creo:feature:7` and `creo:feature:5`;
- orders `0` and `1`;
- name `Creo datum_plane 7`, root class `923`, label `datum_plane`;
- a provenance span whose stream is `AllFeatur`;
- `creo.feature_rows_decoded` true, `creo.feature_row_count` 2;
- `creo.feature_history_decoded` false and `creo.geometry_decoded` false.

The existing container, replay, edited-document, assembly, configuration, damaged-section, stream,
and bad-input tests are unchanged.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Compound-boundary gotcha](../../Gotchas/Conversion/CreoTaggedCompoundBoundary.md)
- [Tagged-stream research](CreoTaggedStreamResearch.md)
