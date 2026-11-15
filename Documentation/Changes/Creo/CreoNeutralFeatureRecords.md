# Creo neutral feature identity records

## Change

Adds `src/convert/adapters/creo/Records.py` and wires it into the Creo reader. The adapter now
decodes `AllFeatur` feature identity rows into neutral `FeatureStep` records instead of returning an
empty feature timeline.

## Behaviour

A feature row is found at offset zero or immediately after a `0xe3` byte. From there the decoder
reads a compact feature identifier and requires the root-schema anchor `e3 f6 <compact-class> e1`
within the next 16 bytes. The class must be a known feature class:

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

Rows shorter than 16 bytes are rejected, which drops the six-byte false positives seen in the
ladder control. The first feature can also be taken from its `e0 01 id 00` definition when its
anchor falls outside the 16-byte window.

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
- Rows without an `e3 f6 <class> e1` anchor are not emitted except for the first feature.
- The production writer is unchanged and still performs exact source replay only.
- `vendor_loadable` and `application_usable` remain false.

## Verification

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
