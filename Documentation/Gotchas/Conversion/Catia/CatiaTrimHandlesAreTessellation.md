# CATIA trim handles are tessellation indices

## Expectation

Trim packet handles are B-rep vertex identifiers, so a handle maps directly to a row in the
`01 06` vertex table.

## Observed behavior

The handles are dense indices into a shared tessellation vertex table.
`Washer_8.CATPart` has eight B-rep vertices but ninety-four distinct trim handles, exactly
`0..93`. `Pedal_Body.CATPart` has 424 B-rep vertices and 2666 trim handles, exactly `0..2665`.

The trim packet is an indexed triangle mesh. Its boundary cycles approximate the B-rep loops but
are not the B-rep loops.

## Workaround

Do not treat a trim handle as a vertex index.
Derive loops from the tessellation boundary only as a documented approximation, and do not claim
native B-rep topology from it.
Reject parts whose surface count does not equal the face count instead of returning a partial
solid.

## Evidence

- `re/catia/Tessellation.md`
- `src/convert/adapters/catia/NativeTopology.py`
- `src/convert/adapters/catia/NativeBrep.py`
