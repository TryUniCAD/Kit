# Blank drawing save and container framing

The generated blank and ordinary front drawings both opened, rebuilt and accepted an edit in SOLIDWORKS `34.5.2.0604`. Both returned `[false,1,0]` at native save and left empty SaveAs targets. Each corresponding reduced native drawing used the same seven logical roles and saved and reopened. The generated drawings share the container profile already used by the successfully saved generated single-occurrence assembly. The disclosed drawing comparisons below test whether that physical profile alone can produce the drawing save failure. [Blank trial](../measurements/2026/GeneratedBlankDrawingSaveModes03.json) · [Front trial](../measurements/2026/GeneratedFrontDrawingNative01.json) · [Assembly trial](../measurements/2026/GeneratedSingleOccurrenceNative01.json)

## Controlled framing comparison

`PrepareBlankDrawingFraming.py` takes the disclosed corpus, the hash-verified seven-role D00 reduction from the earlier save-mode comparison, and an unused output path outside the checkout. It verifies the reduced bytes against both positive native save modes and checks the pristine source and author/reopen records from the blank drawing lock. The paired original and reframed diagnostic files carry the exact same seven decoded streams and the same compressed bytes. [Source lock](../v2026/heldout/DrawingSourceLock01.json) · [Preparation receipt](../measurements/2026/DrawingBlankFramingCandidate01.json)

Each matched archive is 8,734 bytes. The comparison changes only 120 bytes in 30 four-byte words. Those words contain the physical file ID, each local and central signature, the two copies of each stream record's framing word and the end-directory signature. The marker positions come from the container reader. All seven stream hashes, extents, compressed contents, stream offsets and archive version agree. Both variants retain the same exact typed Definition and Header2 with next map indexes 212 and 34. The Kit physical profile uses file ID `0xec6e2386`, and the original reduction uses `0x1d96781c`. The detailed comparison records the exact differing words. [Wire signatures in this release](../v2026/Reverification.md)

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -B \
  re/tooling/sw2026/PrepareBlankDrawingFraming.py /private/disclosed-source-lock \
  /private/previous-trial/Inputs/ReducedNative/D00EmptySheet.SLDDRW \
  /private/unused-framing-packet
```

The staged `Tools/InspectBlankDrawingFraming.py` accepts `Trial.json` and `--packet-sha256`. Its `--verify-only` mode checks the immutable inputs and tool digests. The native comparison uses the existing save-mode observer for SaveAs after rebuild and Save3 after a 3:2 scale edit. Each framing pair uses the same disposable input and target paths within a mode. Fresh reopen measures the expected state before the observer moves that lane's records. The pristine native control brackets both modes. The preparation receipt attests to a source-preserving diagnostic with zero generated writer outputs.

## Native observations

Twelve distinct pinned native processes passed. Both save modes completed with `[true,0,0]` under both framings. Both pairs used exactly matched physical paths and reopened with the expected ratios of 1:1 after SaveAs and 3:2 after the in-place edit. Both pristine brackets passed, all ten live tree rows remained intact, and input hashes stayed immutable. The four derivatives independently re-encoded their full Definition and Header2. The vendor selected a different file ID in each save. [Native framing receipt](../measurements/2026/DrawingBlankFramingNative01.json)

The Kit container profile alone is insufficient to reproduce the save failure on this disclosed sheet. The generated drawings still require localization of the failing native save branch. Earlier open and edit evidence remains scoped to their exact generated inputs.

## Shared save return edges

The pinned `slddrwu.dll` drawing save override at `0x3ded4af0` returns the common save result at `0x3ded53a2` when its preparation succeeds. It can also return zero before that call. The drawing model is retrieved through slot `0x1300`. A missing model returns through `0x3ded4c4a`. A drawing UI helper guarded by a present runtime owner at `+0x1780` and slot `0x1410` is called at `0x3ded4cdc`; failure returns through `0x3ded4ce5`. The common drawing preparation at `0x3df124f0` is called at `0x3ded4def` and has a zero return at `0x3ded4df8`. [Pinned module identity and overall path](DrawingSaveBoundary2026.md)

The preparation helper can return zero on a missing model active sheet at `0x3df1262c–0x3df1263a`. Both generated inputs had an active sheet and a live tree after native rebuild. The separate application-setting check at `0x3df1299f` can also return through `0x3df12eb8`. It occurs in the save-time detailing preparation. The detail-definition values consumed by that preparation, `f220 = 1` and `f224 = 0`, agree in both generated files and both reduced native inputs. They do not account for the observed split on their own.

The shared `slduiu.dll` `uiModelDoc_c::DoSave` at `0x496f76b0` can also reject an explicit same-target save for a frozen model at `0x496f7781`. The drawing's slot `0x1268` resolves to the shared `isModelDocFrozen`. The ordinary route obtains storage at `0x496f77b5` and returns its save result from slot `0x128` at `0x496f77ce`. Earlier paired evidence observed a generated failure both on SaveAs to a fresh target and on Save3 on a writable private copy. It remains necessary to observe whether each failure reaches the drawing preparation, storage or commit stage.

The storage route's `OnSaveDocument` inspects self-reference timestamp state at `0x496fd746`, calls `setSelfRefLastModTimestamp` at `0x496fd76f`, then synchronizes save timestamps and continues. The prerequisite accessor tests bit 1 of `moExtObject_c.f58` at `sldarchiveu.dll` `0x31a01300–0x31a01308`. The generated self reference stores `0`, and the passing reduced native reference stores `8`. The version-19000 load reads the flag byte at `0x319fdcfb–0x319fdd09`, sets runtime bit 8 at `0x319fde32` and clears bits 3 and 1 at `0x319fde47–0x319fde51`. Both observed values yield the same flag state through this routine. Store later computes wire bit 3 from runtime bit 8 at `0x319fd9b8–0x319fd9cd`. [Reference flag normalization](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ExternalReferences/ReferenceFlagsNormalizeOnLoad.md)

The COM wrapper folds each zero return into generic error bit 1 at `0x49793d73–0x49793d7a`. The private oracle currently records that public result and the file extent. The static return edges were checked in a bounded REA/Hopper analysis and independently in the pinned PE. They identify possible boundaries and do not establish a runtime branch trace for the generated failures.
