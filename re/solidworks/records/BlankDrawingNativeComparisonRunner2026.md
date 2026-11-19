# Native runner for the frozen ordinary blank drawing comparator

This is a source-only oracle runner. No private slot, candidate or native source was opened during its preparation. Root alone runs the reserved Windows oracle. Task `B04-SW2026-DRAWPROPS/blank-public-qualification`, delivery PR #121.

The runner retains [BlankDrawingComparison01](../../../re/tooling/sw2026/blank_eval/BlankDrawingComparison01.py) exactly at SHA-256 `38db51428485c1c0b7075cedfe44f76b99f0bf36d0a8c5300141cbb299cacfa7`. The [comparison protocol](BlankDrawingPublicComparison2026.md) and original [source lock](../measurements/2026/BlankDrawingBlindSourceLock01.json) remain unchanged. Full original-source acceptance remains unclaimed.

## Access and native sequence

`Tools.json` binds eight independently authored research tools. Its exact digest must be the final method binding's `native_observer_manifest` before private intent access. The runner first verifies its complete tool closure, method binding, independently verified writer manifest, source-lock metadata and generation freeze. It checks both slots' predictions and all four matching-path generated payload copies before creating the exclusive `AccessGate.json` receipt. No original source path or payload is touched before that gate.

Each native phase runs in a separate Python worker. Every worker rechecks the frozen tool/method/generation metadata and the original access receipt before computing a native input path. Original inputs are fixed to:

```text
C:\KitBlankDrawingSource121\Slot01\Native\Source.SLDDRW
C:\KitBlankDrawingSource121\Slot02\Native\Source.SLDDRW
```

The exact serial order is `ControlBefore`, `Slot01/Source`, `Slot01/Generated`, `Slot02/Source`, `Slot02/Generated`, `ControlAfter`. Each has `OpenEditSave`, then `FreshReopen` in a fresh native process. The runner calls existing `InspectDrawingCache.phase` with the frozen expected tree, initial properties and explicit `edited_ratio` from the sealed neutral prediction. The control uses the independently disclosed D00 tree, 1:1 initial scale and 3:2 edit.

`OpenEditSave` receives the actual input descriptor's hash. `FreshReopen` reads the completed prior worker and untouched raw record by exact hashes, then opens the actual saved derivative with its recorded digest. All native source documents remain read-only. Derivatives go only to an unused, separate guest-local output tree. The runner neither loads a template nor authors native content.

Any measured failure stops dependent candidate phases. A `finally` block independently attempts the trailing control lifecycle, without depending on a failed candidate's state or raw record. A failed first phase skips only its dependent reopen. Workers have a 300-second bound. On timeout Python terminates the worker; the runner does not kill any CAD, license or service process. The independent control still attempts its existing fresh-session guard. If a native process remains alive, that guard refuses activation and records a failed control; root adjudicates the retained process separately. No failure is changed into a healthy control.

After the trailing attempt, the runner rehashes both generated builds, both original sources, both prewriter saved derivatives and the disclosed control. Original edited source paths are `C:\KitBlankDrawingSource121\<slot>\edit\EditedDrawing.SLDDRW`; they are hashed only for custody, not substituted for the fresh derivative. Any mutation fails the comparison.

## Raw records and comparison

The runner keeps `InspectDrawingCache.phase`'s raw `Record.json` unchanged. Its wrapper `Workers/<phase>.json` binds the exact phase name, input digest and raw record descriptor. `Observations.json` has the exact schema accepted by the frozen comparator. It contains ordered phase descriptors `{name,input_sha256,record:{path,sha256}}`; the descriptor file itself is then hashed. The comparator checks 12 distinct native process births, serial intervals, 30 sheet snapshots, 120 ordered tree rows, clean saves, source immutability and cleanup. Missing/skipped/failed records remain failures.

The disclosed `SdkBlankNative02/Inspection/ControlBefore/{OpenEditSave,FreshReopen}/Record.json` files already have the required shape: top-level `result`, `passed`, `first_failure`, `cleanup_errors`, start/finish timestamps; nested `oracle_identity`, tree and snapshots. The raw saved status is a JSON list `[true,0,0]`, although the live helper returns a tuple. Fresh reopen has no `edited` or `save_status` field. No normalization, tuple patch, type relaxation or comparator change is needed.

## Preparation and root invocation

Use the private frozen `Tools/RunBlankDrawingComparison01.py` next to `Tools.json`. `prepare` reads only its own tools and writes metadata/copies to a new packet. It takes the already frozen binding/generation paths and hashes as arguments; it never reads those private files or any native source on the host.

```sh
python -B /absolute/frozen/Tools/RunBlankDrawingComparison01.py prepare --output /unused/BlankNativePacket --tools-sha256 TOOLS_SHA --guest-root '\\Mac\Home\Documents\Research\BlankNativePacket' --guest-python 'C:\verified\python.exe' --guest-output 'C:\KitBlankDrawingEvaluation121\Native01' --guest-control '\\Mac\Home\Documents\UniCAD\Oracle121Takeover\SdkBlankNative02\Inputs\Control\D00EmptySheet.SLDDRW' --binding 'C:\KitBlankDrawingEvaluation121\MethodBinding.json' --binding-sha256 BINDING_SHA --generation 'C:\KitBlankDrawingEvaluation121\GenerationFreeze.json' --generation-sha256 GENERATION_SHA
```

Use actual verified runtime paths and SHA-256 values. The output `Recipe.json` provides exact Windows argument arrays for `verify` and `run`; the source path arrays use the fixed `C:\KitBlankDrawingSource121` slots. After hash-verifying/staging the complete packet, root drives those arrays solely through its existing current-user transport. `verify` reads no original native source and launches no CAD. `run` is the only aggregate native action and requires Windows and the exact configured Python executable.

Terminal files remain inside the declared guest output tree: `AccessGate.json`, append-only `Progress/*.json`, untouched `Native/<base>/<stage>/Record.json`, wrapper `Workers/*.json`, `Observations.json`, `Comparison.json` on a successful comparison, and `Result.json`. `Result.json` retains every phase/timeout status, both controls, raw-record hashes and any comparator/immutability error type. Standard output prints only status, mode and error type; private names/ratios are not printed.

## Actual verification

AST compilation, unresolved-name checks, whitespace and dependency/hash verification passed. The raw-record contract was checked from disclosed old JSON receipts only. No local product/integration test, preparation execution, candidate build, original source access, guest change or native launch occurred. Root must commit the runner before the native run and bind its exact tool manifest before releasing neutral intent. This runner measures only the frozen sheet lifecycle; full source metadata/style/provenance preservation and public-writer acceptance remain separate gates.
