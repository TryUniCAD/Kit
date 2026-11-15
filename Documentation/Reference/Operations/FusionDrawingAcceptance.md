# Fusion drawing acceptance record

This page records what is measured for the Fusion drawing codec against the
[CAD success criteria](CadSuccessCriteria.md), and what is not.
It is an attestation, not a completion claim.

Measured on 2026-11-14 and 2026-11-15 with Fusion 2706.1.17 on macOS arm64.

## C1. No donor data

| Check                                          | Result                              |
| ---------------------------------------------- | ----------------------------------- |
| `tools.Donors.CheckReplays src`                | no recorded payloads in 3078 files  |
| CAD files tracked under `src/`                 | 0                                   |
| Vendor binaries tracked anywhere               | 0                                   |
| Data files under `src/`                        | 16 class vocabularies and defaults  |

The 16 data files are class vocabularies and per-class default tables, not captured document rows.

## C2. No CAD runtime

The reader, the writer and the author are pure Python. The native runs use Fusion only as the
acceptance oracle, never as part of a conversion.

## C3. Lossless

| Check                                                     | Result     |
| --------------------------------------------------------- | ---------- |
| Fusion-saved DWG read and re-emitted byte-exactly          | 60 of 60   |
| Fusion-saved F2D drawing document re-emitted byte-exactly  | 248 of 248 |
| Fusion-saved DWG header typed into parametric variables    | 60 of 60   |

## C4. Fully parametric

The design writer emits a parametric sketch, an extrusion and a BRep body part from a
`DocumentSpec`, and Fusion reports the authored parameter and an exact body volume:

| Case                  | Parameter        | Bodies | Volume cm³ (Fusion) | Volume cm³ (spec) |
| --------------------- | ---------------- | ------ | ------------------- | ----------------- |
| `KitAuthoredCylinder` | `kitLength` 40 mm | 1     | 19.634954084935366  | 19.634954084936208 |
| `KitAuthoredHeldOut`  | `kitHeldOutLength` 27.5 mm | 1 | 5.5292030703178 | 5.529203070318037 |

The drawing side is parametric in the DWG: Fusion applies a sheet extent, a view scale and a view
position that Kit writes, each verified with a one-input control.

## C5 to C7. Loadable, usable, and measured

| Case                                   | Result                                        |
| -------------------------------------- | --------------------------------------------- |
| Kit-authored design, opened in Fusion  | accepted, parameter and volume exact          |
| Kit-modified drawing, opened in Fusion | accepted, sheet 841 by 594 mm, views `[5,4,4]` |
| Kit-modified drawing, view scale       | accepted, first view scale 4.0 to 2.0         |
| Kit-modified drawing, view position    | accepted, every curve moved exactly 20 mm     |
| Kit-authored drawing from nothing      | **not loadable**                              |

The last row is the failure. A DWG header ends with four shorts that Fusion checks, and they are an
encrypted vendor integrity check. The [Fusion donor ban](../../Research/FusionDonorBan.md) forbids
reproducing a vendor integrity check and forbids tracing the libraries that reveal it, so Kit writes
placeholder values and Fusion refuses the file.

## C8. Honest attestation

The loadable row above is a failure, not a partial pass. The save-and-reopen leg is also unproven:
`DataFile.isReadOnly` is true on this Personal Use license, and `saveAs` returns `True` and produces
no file for a design (240 s) or a drawing (900 s).

## C9. Complete implementation

Incomplete. The drawing writer cannot produce a loadable DWG from nothing, and the reason is a policy
prohibition rather than a missing rule.

## C10. Generalization

The design acceptance uses a held-out case with inputs the first case did not use.
The drawing controls change one input each, which is what separates a read value from a constant: all
247 Fusion-saved drawings in the corpus are A3 Landscape at 4:1, so the corpus alone cannot show that
the reader tracks the file.

## C11. Traceable knowledge

| Finding                                        | Record                                                    |
| ---------------------------------------------- | --------------------------------------------------------- |
| Header tail is an encrypted integrity check    | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingHeaderTail.md) |
| Sheet extent comes from the DWG `LAYOUT`       | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingSheetExtent.md) |
| View scale comes from `DRAWINGVIEW` and `SCALE` | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingViewScale.md) |
| View position comes from `VIEWPORT.Center`     | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionDrawingViewPosition.md) |
| Read-only uploads never save                   | [gotcha](../../Gotchas/Conversion/Fusion/Drawing/FusionPersonalReadOnlySave.md) |

## What would change the verdict

Either a document-level field that Fusion accepts in place of the integrity check, or an explicit
decision to lift the prohibition on reproducing vendor integrity checks.
An editable document slot would also let the save-and-reopen leg run.
