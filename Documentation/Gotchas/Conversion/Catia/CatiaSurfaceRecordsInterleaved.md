# CATIA surface records are interleaved with curve records

## Expectation

The `SurfacicReps` stream is a contiguous table of surface records starting at offset 17, so a
parser can walk it from the first record to the last.

## Observed behavior

Surface records are interleaved with curve records. A contiguous walk stops at the first curve
record and silently truncates the surface table.

Measured surface counts from a contiguous walk versus a marker scan:

| Part | Faces | Contiguous | Marker scan |
| --- | ---: | ---: | ---: |
| `4784` | 416 | 4 | 270 |
| `4876` | 870 | 1 | 714 |
| `4876_1` | 870 | 1 | 714 |
| `Pedal_Body` | 338 | 24 | 314 |
| `Reservoir` | 71 | 2 | 56 |

For the 22 parts that already decoded, the contiguous walk happened to reach the end of the surface
section before the first curve record, so the truncation was invisible.

A naive marker scan over-counts by one on `Brake_bias_90_degree_coupler` because a `00 33 <kind>`
byte sequence occurs inside float data and parses as a record. Validate each candidate before
accepting it.

## Workaround

Scan for the `00 33 <kind>` marker with `kind` in `{0x32, 0x33, 0x34, 0x35, 0x38}`, parse each
candidate, and accept it only when:

- the record fits inside the stream,
- the orientation byte is `+1` or `-1`,
- every bounds float is finite and smaller than `1e6` in magnitude,
- the record does not overlap an already accepted record.

This returns exactly the face count for all 22 passing parts and the full surface pool for the five
failing parts.

## Evidence

- `re/catia/Brep.md`
- `src/convert/adapters/catia/NativeBrep.py`
- `src/convert/adapters/catia/NativeSurface.py`
