# Read resolved planar mate selections in SOLIDWORKS 2026

The resolved mate graph binds each plane to the real assembly occurrence and child datum. Its alignment has a separate field. A native save can add component and plane selection strings to the detached planes. The exact object references survive with those strings absent. [Planar wrapper rules](PlanarMateReferenceChains2026.md) · [Alignment rule](PlanarMateInputTranslation2026.md)

| Data | Read rule for the measured version-19000 profile |
| --- | --- |
| Mate list | Load the native model configuration with its bound ModelHeader. Continue its map through ResolvedFeatures and seed MatesList from that final map. Check an exact mate list round trip. |
| Alignment and kind | Take the concrete mate class and `moMate.f3b4`. Observed value 1 means aligned. The independent setter proof also binds 2 to anti-aligned. |
| Endpoint order | Walk the resolved wrappers in `moMateNGeoms_c.f410` order. The owner and both ordinal keys must identify the current mate and endpoint. |
| Occurrence | The wrapper's resolved `moCompRefPlane_c.f58` holds the direct component chain. The `moExtFeature_c` link points back to the live occurrence. Its inherited feature ID matches the XML `swReference.swID` for the root occurrence. The XML object ID yields the portable instance ID. |
| Child configuration | Check the selected configuration ID and name, occurrence and wrapper update stamps, child header and the two stored shared document names. |
| Datum | Resolve the real `moCompRefPlane_c.ff0.f00` in the child ResolvedFeatures. The typed plane's feature ID yields the portable support-plane ID. Keep the stored wrapper origin and normal as archive observations. |
| Driving distance | Traverse the mate's display owner, feature dimension handle and length parameter. The measured A18 display and parameter both give `0.06323 m`. |

## Reproduction

From the repository root, run the projection with the assembly and its synchronized child file. The process reports input digests, the exact round-trip result, ordered endpoint identities, alignment and any measured driving distance.

```sh
PYTHONPATH="$PWD/src" python -B re/tooling/sw2026/serial/ProjectPlanarMates.py /private/input.SLDASM /private/child.SLDPRT
```

Six process runs covered the freshly generated and native-saved coplanar pair, the displaced generated pair and the disclosed A17, A18 and A19 native sources. All six reproduced their mate-list bytes and alignment. The twelve child datum IDs match the public part reader's support-plane IDs, including distinct generated and native datum IDs. The displaced pair preserves its authored 4.73 mm offset in the stored frame. A stale same-name child and a same-name child with the same stamp but a different shared path were both rejected. [Projection receipt](../measurements/2026/PlanarMateProjection01.json) · [Native source lock](../v2026/heldout/AssemblyPlanarMateSourceLock01.json) · [Native mate correction](CoincidentMateActiveSolve2026.md)

The current public assembly reader finds zero endpoints on both fresh generated parents. It finds two through the selection strings after the coplanar parent is saved by SOLIDWORKS. It reports unknown alignment across all six inputs. The probe covers direct resolved part occurrences in one assembly configuration and three disclosed mate kinds. Public adapter integration, nested occurrences and held-out qualification remain open. [Selection string gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/MateSelectionStringsCanBeBlank.md)

An upstream schema trace on the generated pair, its native derivative and the disclosed A18 assembly recorded four provisional rules. Config-0 exercises `moExtFeature_c`, `moExtObjectInterface_c.FUN_4c179410` and `su_CMapStringToString`. ResolvedFeatures reuses the external feature and interface and exercises `moContextChainComponent_c`. The mate lists themselves exercise proven rules. [Assembly archive](AssemblyArchive2026.md) · [Occurrence construction](OrdinaryOccurrenceConstruction2026.md)
