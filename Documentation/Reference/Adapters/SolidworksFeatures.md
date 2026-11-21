# SOLIDWORKS feature resolution

## Purpose and evidence boundary

This reference describes feature-record interpretation and selected research observations.
The observations apply to their recorded source families and vendor builds.
They are not universal offsets for all SOLIDWORKS documents.

## Archive tags

The documented `su_CArchive` grammar uses class and object map entries.
A new class definition and a new object affect the map differently from a reference.

| Tag                                         | Meaning                         | Map increment |
| ------------------------------------------- | ------------------------------- | ------------- |
| `00 00`                                     | Null object                     | 0             |
| `ff ff`                                     | New class definition and object | 2             |
| `0x8000 \| i`                               | Object using class index `i`    | 1             |
| Nonzero object-reference tag below `0x8000` | Reference to an existing object | 0             |

The table describes the short-tag grammar in the linked research.
Consult the implementation for extended tags and version-specific handling.
Initial map indices depend on records that precede the observed stream.
Do not assume that an arbitrary fragment starts at index 1.

## Feature order

The `moCompFeature_c` array records tree-node relationships in the studied families.
The array order matters for rebuild behavior.
Moving physical bytes without correcting those relationships can produce an invalid tree.

The earlier study recorded the following entry-tail fields for a SOLIDWORKS 2025 family:

| Relative offset | Encoding | Recorded meaning       |
| --------------- | -------- | ---------------------- |
| `End - 12`      | `u32`    | Version value `18000`  |
| `End - 8`       | `u32`    | Node identifier        |
| `End - 4`       | `u32`    | Modification timestamp |

These offsets require the documented entry boundary.
Do not apply them as unchecked patches to an unknown file.

## Extrusion observations

The research links extrusion dimensions to scalar records and related end-condition data.
Boss and cut behavior involves class bodies and face-identity information.
The recorded flags `0x40000140` and `0x400201CA` alone do not define a safe conversion.

Selected study offsets include an end-condition byte at `scalar - 818` and a direction byte at `scalar - 824`.
Those values are family-specific observations.
Use the decoded grammar and validation before emitting production records.

## Revolution observations

The studied classes include `moRevolution_c`, `moRevCut_c`, and `moRevEndSpec_c`.
Changing the operation can change the class set and subsequent map indices.
An angle scalar can use radians while presentation metadata uses degrees.
Keep the unit conversion explicit.

The study recorded axis references at `token - 145` and `token - 131` for different axis kinds.
Those locations depend on the documented family and token boundary.
See [revolution research](../../../re/solidworks/features/Revolve.md).

## Typed ordinary 2026 revolve supplement

For the measured modern version-19000 one-direction blind boss, the normal reader can project the actual positive radian parameter and selected construction axis as `AngularRevolve`. The supported contour is a four-line rectangle on the canonical Front datum with an upward construction axis to its left. The axis remains outside the contour and receives no invented anchor; only the four actual horizontal/vertical relations are projected.

The selected axis uses its real sketch-entity path and preserves raw endpoint order, while native reversal controls the effective unit direction. Display caches and KeyWords angle text are presentation rather than driver owners. Ordinary partial Mid Plane projects one total D1 as `symmetric_full`. Ordinary partial Two Directions preserves independent D1 and D2 as `two_sided` with either measured direction. The new end-mode evidence uses a canonical Top datum. Other owner families retain the earlier representation. This supplement adds no writer, native cache or full-tree/held-out qualification. See [the reading guide](../Research/Solidworks/OrdinaryRevolveReading.md) and [exact public-path evidence](../../../re/solidworks/records/SdkOrdinaryRevolveRead2026.md).

## Typed ordinary 2026 edge fillet

The internal ResolvedFeatures reader can explicitly admit the measured single-edge circular fillet after binding its actual Config-0 and CMgr. Four disclosed saves retain their mapped keeper, edge, result-face and driving-radius owners. Public feature projection and native writing require separate evidence. [Explicit edge-fillet reader](../../Changes/Solidworks/Archive/SolidworksTypedFilletRead.md)

## Trace calibration

The historical trace study recorded these archive fields:

| Field          | Recorded offset |
| -------------- | --------------- |
| `m_lpBufCur`   | `0x38`          |
| `m_lpBufMax`   | `0x40`          |
| `m_lpBufStart` | `0x48`          |
| `m_nMapCount`  | `0x50`          |

Recalibrate debugger layouts for a different binary build.
A field name does not establish a stable application binary interface.

## Structural verification

1. Record the source file hash and vendor build.
2. Identify object boundaries from the trace and grammar.
3. Resolve map references symbolically.
4. Recompute indices after a structural change.
5. Compare the re-emitted stream with the expected structure.
6. Obtain remote target-application acceptance evidence.

Byte-identical re-emission supports the segmentation result for that input.
It does not prove complete grammar coverage or editable cross-format translation.

## Cache restrictions

Bounding boxes, display data, and geometry caches can depend on feature parameters.
Do not assume that a stale cache is safe.
Record vendor-version evidence for regeneration before relying on it.
An incorrect cache can invalidate geometry or application behavior.

## Sources

- [Resolved-feature implementation](../../../src/convert/adapters/solidworks/Resolved/Core.py)
- [Archive grammar](../../../re/solidworks/archive/Grammar.md)
- [Segmentation study](../../../re/solidworks/archive/Segmentation.md)
- [Historical imported reference](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/re/solidworks/archive/Grammar.md)
