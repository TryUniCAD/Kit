# Ordinary drawing save boundary in SOLIDWORKS 2026

The generated blank drawing opens, rebuilds and accepts the sheet scale edit in memory. Its save returns `[false,1,0]` and creates a zero-byte target. The reduced native diagnostic saves and reopens after the same operation. The two inputs contain the same seven logical stream roles. The [native trial receipt](../measurements/2026/GeneratedBlankDrawingNative01.json) binds their bytes, the successful native derivative and the bracketing controls.

## Typed archive comparison

The comparison reads the version-19000 typed `Contents/Definition`, standalone `Header2` and the container headers independently. Joined header fields agree between the standalone and inline headers in each input and in the successful derivative. The three archives retain `moHeader_c.fec=1`, the value returned by `getSavedWhileModelExists` at `sldarchiveu.dll!0x31a053b0`. They use next persistent ID `9`, have an ordinary self-file entry of kind `4` with no selected configuration, and retain an unregistered self-file logical ID of `-1`. All have `facc=2`, a sheet sketch in `fac0` and a zero pair in the UI drawing trailer.

| Typed owner | Generated input | Reduced native input and its edited save |
| --- | --- | --- |
| `moHeader_c.f40/f44` | `101/101` | `103/101` |
| `moHeader_c.f98/fcc` | `0/-1` | `1/3` |
| `moHeader_c.f80` license provenance | `0` | `1` |
| Self reference `f58` persisted flags | `0` | `8` |
| `moDrawing_c.fd50` | `1` | `0` |
| `moDrSheet` viewport presence and zone flag `f4d8` | No viewport, `1` | Viewport present, `0` |
| `uiModelDoc_c.f878/f870` | Zero line-style and line-font rows | Seven line-style and forty line-font rows |
| `uiModelDoc_c.faf8/fab8` | No environment or BOM manager objects | One user model environment and an allocated empty BOM manager |
| `uiModelDoc_c.fad4/fb00/fb04` | `3/0/0` | `2/3/38283` |

These differences describe the on-disk inputs. Native load can populate runtime state. The shared UI load adds system line fonts at `slduiu.dll!0x497029a0`, for example. The normal reduced native derivative preserves the listed header state across the scale edit. The records give no causal assignment for the save failure, and license provenance remains governed by the [metadata construction rules](MetadataConstruction2026.md).

Both inputs use container version `4`. The generated blank uses exactly the same file ID, signature triplet and logical type IDs as the generated part and generated single-occurrence assembly in the [assembly trial](../measurements/2026/GeneratedSingleOccurrenceNative01.json). The assembly saved successfully. The reduced native input and its successful derivative use different signatures and type IDs. The physical container comparison supports using the configured format rules for further diagnostics.

## Application call path

The image addresses below are from SOLIDWORKS `34.5.2.0604`. The pinned module hashes are `slduiu.dll` SHA-256 `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`, `slddrwu.dll` SHA-256 `61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47`, `sldappu.dll` SHA-256 `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf`, `doccplu.dll` SHA-256 `ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8` and `sldarchiveu.dll` SHA-256 `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48`.

1. The COM `SaveAs3` wrapper at `sldappu.dll!0x456b2140` dispatches through the wrapped extension's `+0xa90` slot at `0x456b2253`. The shared `uiModelDoc_c::iFileSaveAs` at `slduiu.dll!0x49793260` calls document slot `+0x1d0` at `0x49793d53`. A zero return sets generic error bit `1` at `0x49793d73–0x49793d7a`. The API separately folds in the registered file errors and warnings.
2. The drawing vtable at `slddrwu.dll!0x3e1d6b78` binds slot `+0x1d0` to `0x3ded4af0`. Its drawing preparation handles loaded sheets, display state, previews and linked BOM tables. It calls `uiModelDoc_c::DoSave` at `0x3ded53a2` and retains that result. At `slduiu.dll!0x496f77b5` the shared implementation obtains the document's `ISolidStorage` and calls slot `+0x128` at `0x496f77ce`.
3. `doccplu.dll` binds `SolidStorage_c` slot `+0x128` to `iDoSave` at `0x180012680`. Its native save dispatch at `0x18001641f` invokes document slot `+0x110`, which resolves to `uiModelDoc_c::OnSaveDocument` at `slduiu.dll!0x496fd620`. The save code prepares the self timestamp and path. The base implementation invokes storage slot `+0x10` at `sldappu.dll!0x458e7333`. That slot resolves to `doccplu.dll!0x18001b810`, whose write path calls `SaveToStorage` at `0x18001c64e` or `0x18001c669`.
4. In `SaveToStorage`, display-list save runs at `0x18001dc81`, document properties save runs at `0x18001df56` and ordinary `SaveDefinition` runs at `0x18001e5be`. `SaveDefinition` creates the `Contents` and `Definition` roles and calls the document serializer at `0x1800232dc`. The common CArchive bridge `slduiu.dll!0x497011d0` forwards to `+0x1008` and the drawing serializer at `slddrwu.dll!0x3debc450`. The archive commits through `mthreadStorageCommitter_c` at `0x18001e693` or `0x18001e6b8` and checks for exceptions after each call.

The API result can represent a failure during drawing preparation, stream serialization or commit. A zero-byte target supplies no partial Definition to inspect. A paired probe could distinguish the ordinary save of a writable private input copy, direct SaveAs and SaveAs after the sheet edit using the same fresh-process controls. The first valid divergence would narrow the next owner-specific experiment. Any field intervention on native diagnostic inputs requires an independently frozen output and measured controls. The generated constructor still requires a successful fresh native save and reopen.

## Cosmetic thread presence

The `fd50` mismatch resolves to the `moModel_c` cosmetic-thread presence cache in `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The constructor initializes runtime `+0xd50` to `1` at `0x4c00e16a`. The current-version model serializer calls `getHasCThread` at `0x4c22fced`, stores the result in the cache at `0x4c22fcf2` and emits it as a signed 32-bit field at `0x4c22fcff`. The full-model predicate at `0x4c021800` iterates model features and checks `hasCosmeticThreadFeat` at `0x4c021881`. Lightweight models read the cache. An unlinked blank drawing has no cosmetic thread feature and emits `0`. [Cosmetic-thread cache gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingThreadFlagIsDerived.md)

The isolated corrected candidate reruns the same guarded stdin construction and uses the same Windows self path and all three controls. Both generated Definitions load and reencode exactly at next map index `131`. Their only logical difference is the flag's low byte at observed Definition offset `2566`. The other six streams, container tags, stream roles and SDK sheet inspection agree. Two clean processes generated identical corrected bytes with zero runtime input attempts. [Isolated comparison receipt](../measurements/2026/GeneratedBlankDrawingThreadFlag01.json)

Regenerate the corrected file by running the [blank drawing packet command](GeneratedBlankDrawing2026.md#independent-construction-and-paired-trial) from the corrected source with the same `--windows-path` as the first trial. Use an unused host staging directory. Verify the generated-file pair offline with the same authored request.

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -B \
  re/tooling/sw2026/CheckBlankDrawingThreadFlag.py \
  /private/first-packet/Inputs/GeneratedBlank/KitBlankSheetProbe.SLDDRW \
  /private/corrected-packet/Inputs/GeneratedBlank/KitBlankSheetProbe.SLDDRW
```

## Paired native result

`PrepareBlankDrawingPair.py` stages the frozen baseline and corrected trial packets and verifies their original hashes and offline byte comparison. Run it with `--baseline`, `--baseline-sha256`, `--candidate`, `--candidate-sha256` and `--out`. On the pinned Windows oracle, run its staged `Tools/InspectBlankDrawingPair.py Trial.json --packet-sha256 SHA` using the printed packet hash. Each generated file is copied in turn to the same disposable input path. Both native SaveAs calls use the same output path. When a case saves, the fresh reader opens that exact output before its evidence directory is moved.

Eight fresh SOLIDWORKS processes measured the two generated drawings, the reduced native control and the pristine controls on each side. Both generated inputs had zero open warnings and rebuild problems, matched the ten-row tree, and accepted the 2:3 to 3:2 scale edit. Both SaveAs calls returned `[false,1,0]` and left empty targets. All three controls saved and reopened at 3:2. The field correction leaves the save outcome unchanged. The holds remain sealed. [Paired native receipt](../measurements/2026/GeneratedBlankDrawingThreadFlagNative02.json)

## Save modes

Stage the same pair in a fresh directory. Place `InspectDrawingSaveModes.py` with its staged tools and run it on `Trial.json` through the same Windows oracle. Pass `--packet-sha256` and `--runner-sha256` with the corresponding file hashes. The observer compares SaveAs after the initial rebuild with Save3 after the scale edit. Every in-place save checks that the native model path resolves to the disposable copy and marks that copy dirty. Both modes use the same paths for the generated input and the reduced control.

The reduced native file saved and reopened in both modes. The pristine controls also completed their edit, SaveAs and reopen. In ten fresh processes, every open and rebuild was clean. The corrected generated drawing returned `[false,1,0]` in both modes. SaveAs left an empty target. Save3 left the writable copy byte-identical. The save failure occurs before a scale edit and also on explicit in-place save. [Native save-mode receipt](../measurements/2026/GeneratedBlankDrawingSaveModes03.json)

## Drawing UI omissions

`PrepareBlankDrawingUi.py` takes the pinned previous pair's `Trial.json`,
`--prior-sha256` and `--out`. It decodes and re-encodes only the disclosed
native reduced control's typed Definition, preserving its other six logical
streams. It stages the unmodified repack and four isolated omissions. Run
the staged `InspectBlankDrawingUi.py Trial.json --packet-sha256 SHA` in the
pinned Windows oracle using the printed packet digest. The pristine brackets
and four variants use the same loaded and saved paths across fresh processes.

The viewport, both line tables, and the environment and BOM owner group were
omitted independently and together. All fourteen native phases passed. Each
saved drawing preserved the 3:2 sheet edit and ten-row feature tree. Typed
readback found that the viewport, environment and BOM manager reappeared
when omitted. Empty line style and font tables remained empty after save
and fresh reopen. The reduced native drawing accepted those absent UI states
together. The generated drawing's native save remains unresolved.
[Typed omission and native readback](../measurements/2026/DrawingBlankUiOmission01.json)
