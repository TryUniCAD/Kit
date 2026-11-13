# Five-line blind boss ResolvedFeatures closure

## Scope

This family contains one closed, simple five-line sketch on the Front Plane followed by one blind boss extrusion.
It is bounded to feature ids 26 and 32, direction 0, positive blind depth, and no sketch dimensions.
Construction or fixed entities, other geometries, open or self-intersecting wires, other planes, and other end conditions remain rejected.

## Vendor evidence

The controlled corpus was authored with SOLIDWORKS 2026 `34.5.2`.
The current parts use `_MO_VERSION_19000`; the older writer envelope remains unchanged.
Production never invokes CAD software and does not copy template streams or opaque byte spans.

The principal differential source is `(0,0), (35,0), (42,17), (19,32), (-5,14)` millimetres, with depth 9 mm.
The independent profile is `(5,-10), (45,-5), (35,25), (12,37), (-8,12)` millimetres, with depth 13 mm.
A same-profile 17 mm depth variant isolates four depth-valued doubles.

`re/tooling/harness/AuthorPolygons.vbs` also generates 64 seeded non-self-intersecting profiles.
`re/tooling/harness/OracleMeasure.cs` reads geometry through raw `IDispatch::Invoke` without loading SOLIDWORKS type libraries.
`re/tooling/harness/OracleDrive.vbs` edits the depth directly through the working late-bound API and closes without saving.

## Trace and byte closure

The real stream is 11,205 bytes.
It starts with the continuation value `0x6d`, corresponding to initial map index 109.
The native buffer exposed by CDB can have capacity `0x10000`, so filtering on exact stream length is wrong.
`re/tooling/windbg/Traces/PolylineFiveObjects.txt` therefore identifies the stream by its leading `0x6d`, not buffer capacity.

The exact 2026 `swccu.dll` has SHA-256 `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` and image base `0x31a30000`.
Useful native entries are:

| Reader operation          |      Address |
| ------------------------- | -----------: |
| `su_CArchive::ReadClass`  | `0x31a3a2d0` |
| `su_CArchive::ReadObject` | `0x31a3a550` |
| `operator>>(uchar&)`      | `0x31a34270` |
| `operator>>(ushort&)`     | `0x31a342e0` |
| `operator>>(float&)`      | `0x31a34410` |
| `operator>>(double&)`     | `0x31a34470` |

REA result `ev_62cddcb2f58a67e4ca68078cc0823bd3f696994baf5176892ffbbf69d877c8ad` records 1,309 procedures and 1,270 strings in `swccu.dll`.
Result `ev_68ff5b10754cc221cc281307f887ece271735c7ff16bc2249d674a0117761ab3` records 93,329 procedures and 64,252 strings in `sldmodu.dll`.

The object trace contains 332 `ReadObject` and 332 `ReadClass` events.
The segmenter tiles all bytes with 332 objects, 40 class definitions, base 109, and zero counter mismatches.
Symbolic re-emission is byte-identical, with 30 external class references and six external object references.
Primitive tracing adds 3,169 reads.
The typed program has 2,708 operations across 495 serializer owners and zero uncovered bytes.
`re/tooling/windbg/Generation/CheckResolvedProgram.py` independently verifies re-emission against the original native bytes.

## Semantic fields

Coordinates are little-endian IEEE-754 doubles in metres.

| Meaning                             |                     Offset |
| ----------------------------------- | -------------------------: |
| Point 1 x / y                       |                6121 / 6129 |
| Point 2 x / y                       |                6299 / 6307 |
| Point 3 x / y                       |                6461 / 6469 |
| Point 4 x / y                       |                6623 / 6631 |
| Point 5 x / y                       |                6785 / 6793 |
| Blind depth copies                  | 10012, 10084, 10572, 10596 |
| Negative annotation-depth witnesses |               10410, 10434 |

The point fields were found by matching all ten source coordinates across independently authored profiles.
The depth fields were isolated by changing only 9 mm to 17 mm.
`PadFieldMap()` validates five unique vertices, finite coordinates, simple segment intersections, nonzero signed area, and positive finite depth.
It converts all millimetre values to metres.

The corrected map contains 55 dynamic values: ten coordinate fields, four positive-depth fields, eight bbox fields, 24 display-plane fields, seven rightmost-vertex annotation fields, and two negative-depth fields.
The bbox centres and full sphere diameters are at 8797–8821 and 9027–9051.
The full diameter is `2*sqrt(half_x²+half_y²+half_z²)` in metres. Converting that result to millimetres uses a factor of 1,000, not 2,000.
Display-plane extents follow 1.1 times the body half-extents about the bbox centre.
Annotation witnesses follow the unique rightmost vertex, which is not necessarily the greatest Y coordinate.
A tied rightmost vertex remains unsupported and fails closed rather than guessing attachment selection.

## Application acceptance

The public reader converts the source to neutral Kit JSON before writing.
That avoids saved-source replay and proves construction from the neutral model with `allow_carrier=False`.

All 64 random profiles report `vendor_loadable=true`, `application_usable=true`, and `near_lossless=true`. These flags are internal writer assessments, not independent vendor acceptance results for all 64.

Combining the independently typed feature stream with a compatible 2026 hierarchy opens with one body and native `Sketch1` and `Boss-Extrude1`.

Fresh public generation through `write_document(..., allow_carrier=False)` now passes the bounded SOLIDWORKS 34.5.2 gate.

- Control output: `kit-five-public-control9.SLDPRT`; open and rebuild with zero load errors or warnings; one body; volume 9,189 mm³; area 3,173.38914944295 mm²; depth parameter 9 mm.
- Shifted output: `kit-five-public-shifted37.SLDPRT`; one body; volume 58,830 mm³; area 8,931.49440578137 mm²; depth parameter 37 mm.
- The shifted profile has area 1,590 mm², so its live unsaved `D1@Boss-Extrude1` edit to 17 mm yields 27,030 mm³ and area 5,822.57851076441 mm².
- The live feature enumeration contains `Sketch1` as a profile feature and `Boss-Extrude1` as an extrusion. The edited document closes without saving.

The independently typed 2026 family consists of a 3,816-byte `Definition`, 2,159-byte `CMgr`, and 25,476-byte `Config-0`, alongside the 11,205-byte five-line feature program. The fixed 2026 visual growth is 196 bytes. All later insertion positions must include this delta before applying their own record-specific shifts; using the pre-growth offset corrupts `moTransRefPlaneData_c` in its earlier payload.

This proves bounded editable five-line native generation. It does not imply arbitrary SLDPRT histories, complete SLDASM/SLDDRW support, or acceptance of all 64 corpus profiles.

| Check           |                                          Initial 9 mm file |                                      Unsaved edit to 17 mm |
| --------------- | ---------------------------------------------------------: | ---------------------------------------------------------: |
| Volume mm³      |                                         9189.0000000000018 |                                         17357.000000000007 |
| Area mm²        |                                         3173.3891494429467 |                                         4179.0683933922328 |
| Centre x/y/z mm | 18.619000979431931, 13.016650342801178, 4.4999999999999991 | 18.619000979431931, 13.016650342801178, 8.4999999999999982 |

Two further generated random cases also match their vendor-authored controls:

| Case        |         Volume mm³ |           Area mm² |  Depth mm |
| ----------- | -----------------: | -----------------: | --------: |
| `poly5r064` | 154132.83142880042 | 17348.513279162617 | 41.664951 |
| `poly5r021` | 99696.851273183827 | 14797.292076512411 | 22.022776 |

## Integration and boundary

`src/convert/adapters/solidworks/programs/resolved/polyline/fivepoint/` owns the typed registry and semantic mapper.
The sibling six-point family and the existing revolve features are unchanged.
`tests/convert/solidworks/resolved/SolidworksPolylineFiveTests.py` exercises the real public writer and malformed-input rejection.

No complete SLDPRT, SLDASM, or SLDDRW inversion is implied by this result.
Three separate SLDDRW oracle documents were also authored with 5, 3, and 4 native sheet/view records; they do not establish drawing-reader or drawing-writer support.
Local test suites remain unexecuted in this research workflow; remote PR CI owns test execution.
