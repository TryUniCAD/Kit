# Ordinary full ellipse and blind boss archive

This #121 tranche covers linked version-19000, format-4 ordinary part archives with one full nonconstruction ellipse and one forward blind boss on the actual canonical Front Plane. It verifies the two disclosed source saves and both of their independent D1-edited native derivatives. The exact-build authority is SOLIDWORKS 2026 SP05.2 build 34.5.2.0604. The redacted independent source lock landed in `d3a1134c18027fa8a75676cf3cc7a8b9418395b3` with SHA-256 `e152ceab9e1738d85058e6bc85cb46422b64cf92104b3ad0ba4726bee172a43e`. Qualification uses only the four disclosed files and the six matching COM phase receipts. [Source acquisition](EllipseBlindBossSource2026.md) · [Disclosed lock](../measurements/2026/EllipseBlindBossDisclosedLock01.json) · [Redacted prewriter lock](../measurements/2026/EllipseBlindBossPrewriterLock01.json)

## First stop and measured layout

The unchanged baseline at `b2036eae24408422fb98ac2c949f8389d156b165` consumes the whole Config-0 stream in each of the four sources. ResolvedFeatures inherits its next slot 109. The default linked SDK reader first refuses schema-one `sgEllipseHandle` through `moProfileFeature_c.pd_f80.points.point.h1`. Its declaration and tag begin at 6297, slot 186, and its body begins at 6318. Adding only the known handle base advances past 6328 and then refuses the unregistered inline layout at 6962. The handle occupies class slot 185 and object slot 186. The inline ellipse occupies bytes [6962, 7064) within sketch object 184. It allocates zero map entries. Both positions apply to these four sources.

The exact 2026 model module `sldmodu.dll` has SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its regenerated map identifies `sgEllipseHandle` and `sgEntHandle` at the same serializer `0x4c587800`. The exact static ellipse entry `0x4c586da0` calls the shared segment serializer `0x4c590920` from `0x4c586dd4`. Its store branch uses these named members in this order. [Serialize map](../../data/Serialization/SerializeMap2026.json) · [Historical grammar](../../tooling/sw2026/serial/defs/ResolvedSketch.py)

| Owner | Type | 2026 store label / authority | Observed value or target |
| --- | --- | --- | --- |
| `sgSketch.ellipses` row | u16 | existing generic member flags | 0 |
| `sgSegment.fc8/fcc` | shared compact indices | existing segment base | both 1, same actual seam row |
| `sgEllipse.fd8` | i32 | Rotation, label at `0x4d1c9248` | 1 |
| `sgEllipse.fdc` | compact point index | Center, label at `0x4cddfde8` | row 0, creation ID 2 |
| `sgEllipse.fe0` | compact point index | MajorPoint, label at `0x4d1c9290` | row 2, creation ID 3 |
| `sgEllipse.fe4` | compact point index | MinorPoint, label at `0x4d1c92a0` | row 3, creation ID 4 |
| `sgEllipse.fe8` | compact point index | MajorAntiPoint, label at `0x4d1c92b0` | row 4, creation ID 5 |
| `sgEllipse.fec` | compact point index | MinorAntiPoint, label at `0x4d1c92c0` | row 5, creation ID 6 |

The five native store branches compare the object member as unsigned against `0xfffe` at `0x4c586e46`, `0x4c586f03`, `0x4c586fc0`, `0x4c58707d` and `0x4c58713a`. The larger representation uses a `0xffff` prefix and a following 32-bit value. The opt-in codec admits the observed compact form, positive rotation and flags zero. It requires one ellipse and one mapping through the shared schema-one handle. The re-only handle-only probe establishes that decoding the mapped handle and decoding the inline member are separate operations.

## Profile and driving dimension

The actual `moExtrusion_c` is feature 32, resolved map slot 194. Its only stored feature parent is `moProfileFeature_c` feature 26, slot 182. The support owner is resolved datum feature 2, slot 159, reached through `pd_f78` at slot 191 and its linked inherited unit component. The shared frame reader gives the canonical Front identity transform. COM gives the same support and adds Front Plane to its reported parent list. The COM profile contains one closed contour and one segment and reports no relations. The active sketch's relation batches, loop manager and entity-handle data manager are empty in these saves. The seam still owns its mapped `h1` handle with local ellipse row index 0, `f1c=-1` and `f08=0`.

The sketch point array is in physical ordinal order centre, seam, major, minor, opposite major, opposite minor. The receipt keeps its zero-based ordinals, class and object slots and the separate `f08/f0c` creation words. The three authored points match their COM coordinates and last ID words exactly in both native observations per save. The opposite points equal reflection about the centre to binary64 calculation precision. The two distinct semiaxes and the signed major direction come from the actual indexed points. The point counter is 7 at `f140.f08` and the ellipse counter is 2 at `f140.f14` in all four source observations. The remaining creation state and display words remain recorded as observations.

The live D1 chain is `f818.f18` → `moDisplayDistanceDim_c.f850` → `moFeatureDimHandle_c.ff0` → `ParallelPlaneDistanceDim_c.f28` → `moLengthParameter_c.f58`. The respective map slots, starting at `f818`, are 225, 227, 229, 231 and 233. Persistent dimension ID 27 survives both edits. The active metre values go 0.013125 → 0.019375 and 0.021625 → 0.010875. The original parameter span is [9472, 9538) and the edited span is [9620, 9686). The named driving COM value agrees exactly.

## Seam rule and remaining authority

Every measured sketch seam is the same point for both endpoints and lies on the actual ellipse at positive phase approximately 17 degrees. Model the observed position as `c + (major - c) cos(t) + (minor - c) sin(t)` with its signed axes. The full native cap rim trim is [0, 2π] and its seam lies at the major station, 0 degrees. These are separately owned parameterizations. [Seam gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Geometry/EllipseSketchSeamDiffersFromRim.md)

A near-17-degree literal at `0x4cf85090` is the binary64 value 0.29670597283903666 radians in the exact model module. Five direct references pass it to `sgArcHandle::findUniquePointOnCircle` at `0x4c560e50`. The sixth is in a body that constructs an `sgArcHandle`. A match in this constant pool alone leaves the ellipse creator unresolved. The exported `sgSketch::addEllipse` at `0x4c49b2d0` receives the point indices. The remaining experiment must bind the actual full-ellipse producer of those point indices or independently vary and observe the sketch seam while holding the model's authored centre and directed axes fixed. An independently authored nominal-phase coincidence and an off-ellipse point control can distinguish a fixed phase from a point-selection rule. The production source constructor, body/cache ownership, native candidate lifecycle and public read/write admission retain their own gates.

## Linked proof

The SDK's explicit `ReadEllipses` lane reads the complete Config-0 and ResolvedFeatures streams under the actual ModelHeader and CMgr link. Ordinary format/version, actual inherited part, compression mode and CMgr `f658=1` gate the profile. Config-0 retains 108 entries and ResolvedFeatures retains 238. The inherited map uses the exact same entry identities. All eight native stream replays use the existing typed emitters, compare complete bytes and preserve every archive slot and object or class identity. Existing modeled byte fields are listed by owner in the receipt. The default circle and rectangle controls also re-emit both streams exactly and refuse explicit ellipse admission. All guarded processes use zero external accesses. [Numeric archive receipt](../measurements/2026/EllipseBlindBossArchive01.json)

```sh
python3.14 -I -B re/tooling/sw2026/ellipse_source/AuditEllipseArchive.py \
  --disclosed-root /absolute/path/to/DisclosedNative
```

The deterministic worker accepts the exact disclosed lock, registered API receipt, six phase reports and four named CAD hashes. It validates custody before opening the in-memory format, compares actual linked owners against measured COM rows, and prints numeric and identity evidence. The generic research CLI lacks a typed sketch member and map-event observer. The dedicated worker uses the existing source-lock and file-read audit machinery to track that view. [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Corpus-correlation playbook](../../Playbook/CorpusCorrelation.md)
