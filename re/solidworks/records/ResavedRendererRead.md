# Resaved part appearance allocator diagnosis

Task `A12b-ResavedRendererRead` owns this research command and evidence only. The SOLIDWORKS encoder boundary lane owns delivery, with PR #121 retaining the Definition and appearance codecs. The preparation base is PR #316 at `0d1f6633e6e9e834a200d3c02990b3dea3174c9b`. This tranche ends with repeatable codec and refusal observations; ordinary admission, source conversion and native qualification are not changed.

## Measured boundary

The named composite's previously measured native save has SHA-256 `15fbc8da9c56d5b1a99e8f568de369fd9b992e40386a04c577ab8c0e2d45e356`. Its 857-byte Definition is `99e7d629b1cb52b1b12b8a0818aee73a38578e039ede1bb7e4a823da3d7163d9`. The ordinary reader consumes the stream before `ReadModelDef` calls `CheckDefScope`, which calls `CheckDefRender`. The latter refuses because the present embedded `PWMaterialManager_c` has `f08=4`, rather than its narrowly admitted part value 6. The high word is zero and the reference list is exactly empty.

The existing [Definition journal](../WriterResearch/DefinitionJournal.md#appearance-id-counter) identifies `f08/f0c` as the signed low/high halves of the unsigned64 next-appearance allocator. They are not a renderer-mode enumeration. PR #121 already owns `ReadEmptyAppr`, `MakeAppearMgr` and the typed `AppearanceState`. This study invokes that existing owner rather than inventing a field rule or discarding the manager. A zero reference count does not establish that other document streams contain no appearance state.

| Disclosed case | Presence and next ID | Ordinary Definition result |
| --- | --- | --- |
| Author04 baseline | Present, 6 | Admitted |
| Named generated composite | Absent; typed implicit initial ID 1 | Admitted |
| Named native save | Present, 4 | Refused |
| Earlier Top native save | Present, 4 | Refused |
| Plane literal-On native save | Present, 4 | Refused |
| Earlier saved Kit edit | Present, 4 | Refused |
| Forward-plane before snapshot | Present, 7 | Refused |
| Inverse-plane on snapshot | Present, 11 | Refused |

All eight complete Definition streams re-emit byte for byte with the existing general codec. Every map slot retains its actual class or object identity. The seven present managers have zero reference rows and re-emit exactly through the existing empty-owner constructor. The [recorded report](../measurements/2026/ResavedRendererRead.json) retains each original hash, Definition hash, map digest, counter and separate outcome.

PR #121 at `c0a401a607759fb0c2589647c2a22af65ebb7ce1` defaults `ReadModelDef` to `OrdinaryOnly=False`. Its explicitly ordinary call and the frozen PR #316 reader retain the six refusals. General-codec completion is not ordinary admission. The frozen public `open_document(strict=True)` separately returns a document in all eight cases, with the recorded configuration, linked D1 and informational diagnostics. These observations neither bypass the ordinary guard nor establish complete presentation or source admission. [Public/ordinary distinction](../../../Documentation/Gotchas/Research/Writers/SolidworksEmptyAppearanceManagerKeepsItsAllocator.md)

## Reproduce without a CAD application

Use clean checkouts at both exact reader revisions and Python 3.14.6. Keep the private input manifest outside the repository. Its root has `schema: kit.research.resaved-renderer-read.v1` and a nonempty `cases` array. Each case contains only `name`, an absolute disclosed `.SLDPRT` `path`, and lowercase `sha256`. Names are unique ASCII identifiers. No source bytes, raw native paths or vendor software are included in the tracked report.

```powershell
python -I -B re/solidworks/RendererBoundary/InspectResavedRenderer.py inspect --manifest $inputs --dependency-root $reader121 --ordinary-root $reader316 --output $unusedOutput
```

The command reuses the existing input/report helpers and pinned-dependency guard. Four independent worker processes select the general codec, PR #121 ordinary scope, frozen Definition scope and frozen public SDK read. Inputs and reader revisions are rechecked before and after the cohort. General and ordinary Definition inspection has a guarded in-memory stage after SDK imports and text-codec initialization. The public SDK comparison is reported separately. The command launches no native application and emits no candidate archive; exact re-emission is an in-memory codec check only.

Two final command runs produced identical `Report.json` SHA-256 `54a70755349c7bfb816550128b9ae38659548dee8b4f11bcbe4d27b0d9f10ee0`. The method hash is in that report. A wrong dependency and a wrong native digest each exited 1 before output-directory creation. Their private summary has SHA-256 `3e28f5cda0cfe128f4c7ce696ed31795e0de5f531232db9b35555cf0b68732cf`. Earlier initialization-only attempts and the superseded first report remain private and are not these final results.

## Private recovery and remaining work

The private evidence holder retains `ResavedRendererRead01/RendererInputs.private.zip`, 300,268 bytes, SHA-256 `2e5785fe96fb97c8766ff697ec9f41be7230752058f0c9acc5c3b3b1d2477856`. Its twelve members are the eight approved CAD inputs, private input manifest, two matching reports and negative-check summary. `Custody.private.json`, SHA-256 `bfb97680323aa04376d4ad8ee091fe94c40a85b64b3c2226f836003130a3c65e`, binds every member to its original path, size and hash. Every archive member was reread and compared, and all eight original inputs were rehashed after packaging. No installed software is retained. Extract only to an unused private directory after verifying the archive and inventory hashes. Repointing private input paths changes the manifest digest; it must not be described as byte-identical report custody.

A future isolated change could coordinate with PR #121 to validate the ordinary part's empty appearance manager through its existing owner-preserving typed semantics. It must preserve both allocator halves, exact presence and empty-list validation, and retain populated/foreign-owner, unrelated UI and assembly boundaries. The observed counters are evidence, not a whitelist or a factory default. Product extension requires the parent owner's approval and separate acceptance. No new held-out input, native run, full-source conversion or public writing qualification occurred here.

## Replay the empty allocator in a fresh Definition

Use the named native save from the private custody record above. Set `$source` to that exact archive, `$reader121` to an unmodified checkout of `c0a401a607759fb0c2589647c2a22af65ebb7ce1`, and `$out` to a new scratch directory outside the checkout. The three commands run in separate fresh Python processes. Each output path must be unused.

```powershell
New-Item -ItemType Directory -Path $out
$replay = 're/solidworks/RendererBoundary/ReplayEmptyAppearance.py'
python -I -B $replay --dependency-root $reader121 extract --source $source --output "$out/Source.json"
python -I -B $replay --dependency-root $reader121 generate --request "$out/Source.json" --output "$out/Source.definition"
python -I -B $replay --dependency-root $reader121 verify --request "$out/Source.json" --definition "$out/Source.definition"
```

The extractor checks the archive and Definition digests, format 4, archive version 19000, concrete part schema one and the existing typed empty-list rule. Its canonical output is `{"AppearanceValue":{"ManagerOnWire":true,"NextAppearanceId":4}}` plus a newline. This is the existing [PR #121 appearance state shape](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/re/tooling/sw2026/throughempty/ManagerProcess01.py).

Generation receives the JSON only. Independent settings select ISO drafting, plane bit 17, tessellation `(26, 4, 25, true)`, environment preference false, journal title `Journal` and density `1000 kg/m³`. The current typed factories construct a fresh Definition and derive the empty manager representation. Readback checks both signed halves, the count and rows, map identity in typed re-emission and bytes against the independent settings. The input archive belongs exclusively to extraction.

The [offline report](../measurements/2026/EmptyAppearanceReplay.json) binds the method, pinned codec, source and all fragment digests. Two process runs reproduced all four cases. For the controls, write the same canonical JSON fields with `(ManagerOnWire, NextAppearanceId)` set to `(false, 1)`, `(true, 1)` or `(true, 9223372043297226759)`. Pass each request through generation and verification in separate processes. Generation refused `(false, 4)` and an extra `references` field before output. Verification also refused an absent request paired with a present fragment at the same counter. [Exact integer and presence gotcha](../../../Documentation/Gotchas/Research/Writers/SolidworksAppearanceAllocatorRequiresExactJsonIntegers.md)

The generated artifact is a Definition fragment. The probe leaves appearance references in the model, configuration and VisualStates outside its scope. It establishes neither full source reconstruction nor native acceptance. The ordinary and public reader boundaries described above still apply.
