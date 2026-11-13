# Native five-line blind boss histories

## Behavior

Kit now constructs a native SOLIDWORKS blind boss extrusion from a closed, simple five-line sketch on the canonical front plane.
The writer selects this program only for feature IDs 26 and 32, direction zero, blind termination, no construction or fixed geometry, and no sketch dimensions.
The reader reconstructs an ordered polyline and its driving depth.
Other profile lengths, profiles containing other geometry types, and unrecovered end conditions continue to fail closed.

## Native data model

The program represents every `Contents/Config-0-ResolvedFeatures` byte through typed operations.

| Measurement       | Result |
| ----------------- | -----: |
| Stream bytes      | 11,205 |
| Archive objects   |    332 |
| Class definitions |     40 |
| Initial map index |    109 |
| Typed operations  |  2,708 |
| Serializer owners |    495 |
| Missing bytes     |      0 |

The ten point-handle fields sit at offsets 6121, 6129, 6299, 6307, 6461, 6469, 6623, 6631, 6785, and 6793.
Four depth copies sit at offsets 10014, 10086, 10574, and 10598.
The central helper is `src/convert/adapters/solidworks/programs/resolved/polyline/fivepoint/Program.py`.

No vendor stream, template, opaque payload, COM call, CAD runtime, or encoded donor stream is used by production conversion.

## Verification evidence

[The research closure](../../re/solidworks/records/PolylineFivePad.md) records the exact binaries, trace filters, field ownership, and reproduction tooling.

- REA evidence `ev_62cddcb2f58a67e4ca68078cc0823bd3f696994baf5176892ffbbf69d877c8ad` covers `swccu.dll` with 1,309 procedures and 1,270 strings.
- REA evidence `ev_68ff5b10754cc221cc281307f887ece271735c7ff16bc2249d674a0117761ab3` covers `sldmodu.dll` with 93,329 procedures and 64,252 strings.
- Traced stream segmentation tiles completely, re-emits byte-identically, and has zero counter mismatches.
- Independent typed re-emission produces SHA-256 `58f24db25ce3a7069b511e2b551ead8228234971932fc95a28a7d5e264020bab`.
- Sixty-four seeded five-line profiles all pass through public native writing: `records: 64, passed: 64, failed: 0`.
- The generated 9 mm part opens in SOLIDWORKS 34.5.2 with one body, native `Sketch1` and `Boss-Extrude1`, and volume 9,189 mm³.
- Editing `D1@Boss-Extrude1` to 17 mm rebuilds to 17,357 mm³ and centre of mass `(18.619000979431931, 13.016650342801178, 8.4999999999999982)` mm. The edit is not saved.

Two randomly selected generated parts have these oracle measurements:

| Generated part         | One body |         Volume mm³ |           Area mm² |  Depth mm |
| ---------------------- | -------: | -----------------: | -----------------: | --------: |
| `kit-poly5r064.SLDPRT` |        1 | 154132.83142880042 | 17348.513279162617 | 41.664951 |
| `kit-poly5r021.SLDPRT` |        1 | 99696.851273183827 | 14797.292076512411 | 22.022776 |

These values agree with the corresponding vendor-authored models at floating-point display precision.

`tests/convert/solidworks/resolved/SolidworksPolylineFiveTests.py` covers strict public writing, decoding, typed frame closure, and fail-closed open and self-intersecting profiles.
Local test suites were not run; current remote CI evidence belongs in the PR.

## Limits

No arbitrary sketch family, assembly/drawing coverage, or complete format inversion is claimed.
The new grammar was traced from `_MO_VERSION_19000` vendor files; existing older stream envelopes are unchanged.
The adapter's other supported native families remain intact.

## Linked information

- [SOLIDWORKS feature resolution](../Reference/Adapters/SolidworksFeatures.md)
- [Five-line resolved-record closure](../../re/solidworks/records/PolylineFivePad.md)
- [Archive buffer guard gotcha](../Gotchas/Conversion/SolidworksArchiveBufferGuards.md)
- [Oracle late-binding gotcha](../Gotchas/Conversion/SolidworksOracleLateBinding.md)
- [REA startup timeout gotcha](../Gotchas/Conversion/ReaStartupTimeout.md)
