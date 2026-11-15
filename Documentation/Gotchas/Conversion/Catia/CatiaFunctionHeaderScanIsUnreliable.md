# CATIA function headers cannot be found by a domain-byte scan

## Expectation

`CATMathFunctionGeneral::UnStream` reads a domain byte (`0x41` 'A', `0x47` 'G', `0x46` 'F', `0x43`
'C') followed by a little-endian u16 type. A scan for that pair should locate every serialized
function, including the two functions in a `CATPCurveEquation` record.

## Actual behavior

The scan produces many false positives because little-endian floats and doubles contain `0x41` and
`0x43` bytes. In `4784` the `SurfacicReps` domain-C hits at 8329, 8611, 8893, 9175, 9457, 9739, and
10021 are spaced exactly 282 bytes apart, which looks like a record stride. The bytes at 8329 are
`43 41 00 42 e0 3d d8 62`, which is the tail of a float run, not a function header. The same scan
over `MainDataStream` returns five 'A' hits and three 'F' hits, all inside body records and the trim
chain.

## Workaround

Do not use a domain-byte scan to locate function records. A function record has to be reached by
parsing its container, because the domain byte is not a reliable marker. The `CATPCurveEquation`
record is still not located in `MainDataStream`, `SurfacicReps`, or any of the 41 outer streams of
`Reservoir`.

## Evidence

- `re/catia/FeatureGraph.md` section "The domain-byte scan is unreliable".
- `CATMathFunctionGeneral::UnStream` at `0x18000d9b0` in `CATAdvancedMathematics.dll`.
- `src/convert/adapters/catia/NativeBrep.py` `ParseCircles` and `AssignSurfaces`.
