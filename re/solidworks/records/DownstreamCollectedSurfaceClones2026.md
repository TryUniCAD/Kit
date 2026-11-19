# Collected downstream surface clones, SOLIDWORKS 2026

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID` is delivered in [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root owns the modeled copies and native qualification. The [numeric evidence](DownstreamCollectedSurfaceClones2026.json) pins 2026 SP05.2 build `34.5.2.0604`.

## Acquiring the surface representation

The edge role constructor calls `moFace::getSurfaceId` at `0x4be9b1f0`. In the ordinary branch it reads the actual face attribute and obtains the representation through the kernel wrapper. The Parasolid environment constructor enables the newer surface-ID path at runtime offset `+0x198`. This path sends the attribute's data to the installed ID helper.

The UI and core initialization paths install `moEntityIdHelper_c`. Its slot `+8` reaches `0x4c6c3300`. Primary ID kind 40 reaches the cap allocator at `0x4c6c3cb9`. Kind 74 reaches the sketch-entity surface allocator at `0x4c6c47d2`. Both construct a fresh representation. Repeating a lookup for the same face in this branch can allocate another object with the same identifying values.

The constructors take feature identity and creation time from the integer data. They take the file owner from the first pointer in runtime attribute pointer field 1. The selected edge role assignment retains the actual returned representation after its live-owner check. The source path from persisted local kernel attributes to that runtime file pointer remains an independent dependency.

## Copying the collector result

The collector calls clone slot `+0x280`. The cap dispatch reaches `0x4c6cf810` and the sketch-entity dispatch reaches `0x4c6cfbe0`. Both allocate their representation and copy the feature keeper through `0x4bb5d230`. The keeper copy invokes `moFR_c` copy at `0x4bb343e0`. A nonnull file owner receives its own `moExtObject_c` copy at `0x319fb0e0`, then its referenced configuration is assigned from the source.

| Field | Classification and copy rule |
| --- | --- |
| Surface kind, sketch marker, cap selector and contour | Derived from the corresponding source representation. Modern ordinary cap carries its contour. The cap clone's legacy contour adjustments remain outside the exercised profile. |
| Feature reference ID and creation time | Copied from the actual feature keeper's typed values. The runtime keeper flag stays in memory. |
| File reference | A fresh object for each clone with a live source. Its shared file definition retains the same identity. |
| File `f48,f4c,f50,f54,f58,f70` | Copied from the source object's corresponding fields. |
| File `f60` | Zero on copy construction. |
| File `f78` | The copy starts unindexed at `-1`. |
| Referenced configuration | Name and ID assigned from the original actual file-reference owner. |

The three archived file copies in each scoped witness preserve shared name and path handles with distinct file object slots. The ordinary raw feature-keeper body writes the typed file reference followed by the signed feature ID and the creation-time word. The embedded flag set to `0x10` by a fresh feature-owned constructor is outside that wire body. [Standalone local ownership](DownstreamLocalOwnerContext2026.md) · [File-copy gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Downstream/CollectedSurfaceCopiesStartUnindexed.md)

## Guarded replay

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  python -B -m downstream.CheckCollectedSurfaceClones 1
```

Run the same command with variant `2` for the second generated part. Two fresh processes per variant reproduce the bytes and check the three copied file references. Both old surface-reference exercises retain exact receipts. Each guarded run preserves eleven generated part streams and records zero runtime external operations. [Measurement receipt](../measurements/2026/DownstreamCollectedSurfaceClones01.json)

The exercise uses three explicit members in the research cache body. The [membership source](DownstreamIdentityMembership2026.md) binds first-seen selection and transfer. Complete geometry membership, later remapping and vendor persistence require further evidence. This tranche adds zero vendor runs, held-out qualifications or corpus conversions.
