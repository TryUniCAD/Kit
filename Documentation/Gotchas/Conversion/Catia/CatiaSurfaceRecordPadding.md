# CATIA surface records include three trailing bytes

## Expectation

A `SurfacicReps` plane record ends after the orientation byte.
The next record starts at the next byte.

## Observed behavior

A plane record is 49 bytes, not 46.
The orientation byte is followed by three bytes that belong to the record.
A parser that stops at the orientation byte reads the next record three bytes early and
desynchronises.

The same three-byte tail is present on cylinder, cone, sphere, and torus records.

## Workaround

Use the fixed record length for the surface kind:

| Kind | Length |
| --- | ---: |
| plane | 49 |
| cylinder | 73 |
| cone | 73 |
| sphere | 65 |
| torus | 77 |

Read the orientation byte at `length - 4` and advance by `length`.

## Evidence

- `re/catia/Brep.md`
- `re/catia/tooling/ParseBrep.py`
- `src/convert/adapters/catia/NativeSurface.py`
