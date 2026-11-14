# CATIA trim packets do not start at offset zero

## Expectation

The first `01 4x` signature in `MainDataStream` starts the trim packet chain.

## Observed behavior

The preamble contains false `01 4x` signatures.
A forward scan from offset zero finds a false packet and fails at the first missing trim total.
The real chain starts later and ends exactly at the face-outer-bound run.

## Workaround

Walk backwards from the face-outer-bound offset.
Accept the chain of exactly one packet per face.
The chain start is the first packet in that reverse walk.

## Evidence

- `re/catia/Brep.md`
- `re/catia/tooling/ParseBrep.py`
- `src/convert/adapters/catia/NativeTopology.py`
