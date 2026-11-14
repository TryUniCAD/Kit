# CATIA trim handles are tessellation indices

## Finding

The handles inside a `MainDataStream` trim packet are not B-rep vertex identifiers.
They are dense indices into a shared tessellation vertex table.

Evidence from the corpus:

| Part | B-rep vertices | Trim handles | Dense `0..N-1` |
| --- | ---: | ---: | --- |
| `Washer_8.CATPart` | 8 | 94 | yes |
| `Bolt_M5x40.CATPart` | 28 | 174 | yes |
| `Pedal_Body.CATPart` | 424 | 2666 | yes |

A washer with eight B-rep vertices has ninety-four distinct trim handles.
The handle set is exactly `0..93`, so the handles index a table of ninety-four entries.
That table is not the `01 06` vertex table, which has eight rows.

## Consequence

The trim packet is an indexed triangle mesh that tessellates the face.
Its boundary cycles approximate the B-rep loops but are not the B-rep loops.
Mapping a tessellation boundary to a native B-rep edge requires a linkage that is not yet decoded.

The current reader derives loops from the tessellation boundary and maps handles modulo the
B-rep vertex count. That produces a valid neutral model for simple parts, but it is a derived
approximation, not the native topology.

## Edge rows are polylines

The edge table rows are not two-endpoint edges. Each row is `02 <arity> <handle[arity]>`, and
`arity` is the number of tessellation points along the edge. `Washer_8.CATPart` has arities
`11, 11, 11, 11, 14, 14, 9, 14` and a handle sum of 103.

Edge handles and trim handles share one global point-id space but are not identical sets:

| Part | Edge handles | Trim handles | Same set |
| --- | ---: | ---: | --- |
| `Washer_8.CATPart` | 93 | 94 | no |
| `Bolt_M5x40.CATPart` | 130 | 174 | no |
| `Pedal_Body.CATPart` | 1698 | 2666 | no |

The trim mesh adds interior points that no edge polyline uses. The coordinate table for this
shared point-id space is not yet located.

## Surface pool

Surfaces are also shared. `Pedal_Body.CATPart` has 24 surface records and 338 faces.
The face-to-surface reference is not decoded, so the reader rejects parts whose surface count
does not equal the face count instead of returning a partial solid.

## Surface record length

The record length is not constant per kind. Two cylinder records with identical five-byte
headers in `Washer_8.CATPart` measure 73 and 70 bytes. The three-byte difference is an
unresolved trailer rule.

## Open work

1. Locate the shared tessellation vertex table and its coordinate encoding.
2. Decode the tessellation-to-B-rep edge linkage.
3. Decode the face-to-surface reference for shared surface pools.
4. Resolve the surface record trailer rule.

## Evidence

- `re/catia/tooling/ParseBrep.py`
- `src/convert/adapters/catia/NativeTopology.py`
- `src/convert/adapters/catia/NativeBrep.py`
