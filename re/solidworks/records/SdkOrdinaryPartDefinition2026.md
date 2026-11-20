# Ordinary SOLIDWORKS 2026 part Definition codec

Task `B04-SW2026-DEFINITION` advances the PR #121 writer program on the isolated `codex/solidworks-ordinary-part-definition` branch. The local delivery base is `16493de95602b732a569923ec89cfee13a87d45d` from PR #199. The current archive supplies the shared base, branch and repeat actions. The historical independent constructor and evidence are pinned at `81aff00e947ef3bb39fb479c265782d7ca7a0581`. [Current archive field actions](../../../Documentation/Changes/Solidworks/Archive/SolidworksConfigFieldActions.md) · [Earlier Definition research](Definition.md)

## Format and construction

The stream begins with five signed words and a 16-byte part CLSID. The CLSID selects the untagged schema-one `uiPartDoc_c` root. The archive version is 19000. Its independent object map starts at one and first allocates a class and object for the drafting standard. The ordinary part reader requires complete stream consumption. The writer computes the framed text, row counts, class and object tags from the typed fields. [Typed reader](../../../src/convert/adapters/solidworks/Archive/Definition/ReadModelDef.py) · [Typed writer](../../../src/convert/adapters/solidworks/Archive/Definition/WriteModelDef.py)

Fresh generation begins with `MakePartDef(ModelDefInput(...), density)`. Its explicit inputs are the drafting standard, display bit positions, three tessellation levels, optimal tessellation, the compression preference, the journal name and positive density in kilograms per cubic metre. On the basic profile, recorded factory defaults are `26, 4, 25, true` for tessellation, false for the compression preference, and `1000` for density. The two signed display words derive from the actual bit positions. The journal name uses CString framing and its runtime class schema is zero. [Fresh constructor](../../../src/convert/adapters/solidworks/Archive/Definition/Construction/MakePartDef.py)

| Emitted owner | Field source and evidence |
| --- | --- |
| Tessellation and root | `fa58/fa5c/fa60/fa64` come from the typed input. The ordinary UI constructor supplies prefix `fa74=1`. The part class determines the CLSID. |
| Active view, model data and appearance | The ordinary fresh document has no UI sketch, OLE content, alternate scene, renderer or variation. Its two transforms are identity with neutral scale. Its style and environment lists are empty, with a concrete empty line-font manager. |
| Drafting and display | `fba8` instantiates the requested schema-one standard. `fad8_0/fad8_1` contain the low and high portions of the authored mask in signed 32-bit form. |
| Remaining UI head and tail | The scalar defaults use the version-matched `uiModelDoc` initializer at `slduiu 0x497486b0`. Each empty text or collection is represented by its independent typed owner. `f1370` uses the PhotoView options initializer at `0x4a3082c0`. |
| Notebook | The notebook constructor and reset at `0x4a01d940` and `0x4a023f30` establish the two state words and empty lists. Journal initialization at `0x4a01d6b0` supplies the zero event and state. The runtime descriptor at `0x4aef6660` establishes journal schema zero. |
| Density | The part-specific field `f1688` carries the explicit finite positive binary64 value. The constructor `sldprtu 0x33374980` and density getter `0x3338a480` establish its ownership. Physical body mass has a separate density owner. |

The source record `ModelConstruction2026.md` at the pinned historical revision binds those addresses to SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. `SdkModelDefinition2026.md` gives the complete historical field ledger. `SdkPartPreferenceDefaults01.json` binds the factory initialization ranges. `SdkDefaultPartNative01.json` records the historical 459-byte stream fingerprint in the independent public Skew and Step candidates. Retrieve those records from that revision for provenance. The current author phase receives only explicit in-memory intent.

```sh
git show 81aff00e947ef3bb39fb479c265782d7ca7a0581:re/solidworks/records/SdkModelDefinition2026.md
git show 81aff00e947ef3bb39fb479c265782d7ca7a0581:re/solidworks/measurements/2026/SdkPartPreferenceDefaults01.json
```

## Saved-object scope

The typed reader retains populated line styles, fonts and environment objects when it recognizes their actual layouts. The splitter reads a row count from `f08` and a column count from its enclosing `f0c`. The shared repeat writer checks both counts against their typed collections. Neither repeat adds a length prefix. Standard object lists, model data, geometry and fonts use the active archive layouts. CString and DWord arrays use shared counted-container rules. [Splitter layout](../../../src/convert/adapters/solidworks/Archive/Definition/Fields/DocEnvironmentFields.py) · [Shared container layouts](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/ContainerFields.py)

The disclosed L1 and D19Annulus saves each include a present renderer wrapper with two signed words `(6, 0)` and an empty object list. The reader and re-emitter preserve those saved fields. This narrow profile accepts only that empty wrapper or an absent branch. The values `6` and `0` select the measured saved profile and do not become fresh defaults. The fresh constructor derives branch absence from the absence of authored rendering content. The scope guards reject populated rendering, alternate flags and optional scene, sketch, OLE or variation objects. [Renderer scope guard](../../../src/convert/adapters/solidworks/Archive/Definition/CheckDefRender.py) · [Saved empty renderer gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/EmptyDefinitionRendererWrapper.md)

## Canonical tag boundary

The ordinary Definition reader requires the canonical store width of each
tag. The shared native parser also recognizes an escaped small map
reference and escaped null. Without a width check the typed graph would
discard information and re-emission would shorten those tags. The check
runs before cursor advance and map application. The policy belongs to
Definition and leaves native widths at and above the escape threshold valid.
[Exact tag grammar](https://github.com/TryUniCAD/Kit/blob/a93bb38bb3e51529c57872028f606588a5c54c61/re/solidworks/records/ArchiveTagGrammar2026.md)

The queue cases run all twelve original guarded profile refusals. They
also use separate processes to author a mapped line-style reference
and reject independent escaped alternatives to its low-index object
and class references. The receiver requires the original compact tags
to replay exactly and verifies each expanded tag's underlying reference
with the shared compatibility decoder. These cases await queue evidence.
[Width gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/DefinitionTagWidths.md)

## Guarded measurement

| Case | Stream size (bytes) | Next map index | Status |
| --- | ---: | ---: | --- |
| Independently authored ordinary options | 459 | 7 | Exact prior Skew and Step stream digest and exact typed re-emission |
| Independently authored varied options | 1,037 | 7 | Signed display words, 295-unit Unicode journal and authored density survived exact re-emission |
| Disclosed L1 boss native save | 3,816 | 60 | Exact typed re-emission |
| Disclosed D19Annulus native save | 3,816 | 60 | Exact typed re-emission |

Two author workers receive explicit values on stdin. Two separate reader workers recover those values and reproduce the bytes and map. Another author worker repeats the Unicode case independently. A sixth worker records twelve explicit refusals, including assembly root, alternate schema or version, trailing bytes, renderer scope, scene owner, zero density and an out-of-range display bit. Only then does the supervisor obtain the two hash-pinned disclosed files from Git and hand them to separate readers. Each saved stream contains seven line styles, forty fonts and splitter grids of `1×1` and `2×1`. All eight isolated workers recorded zero guarded external access attempts after imports. The source blobs and exact stream digests are in the receipt. [Guarded proof](../../tooling/sw2026/definition/ProveOrdinaryPartDef.py) · [Numeric and digest receipt](../measurements/2026/SdkOrdinaryPartDefinition01.json)

The original receipt SHA-256 is `12ffb0f2b69543367634e8dda7028cc0b951016816e755452eb0e04c63a6d891`. It binds the pre-review implementation and worker at `e6540b325e056a820009c3d52752a9d994423a48`. [Pinned receipt and source manifest](https://github.com/TryUniCAD/Kit/blob/e6540b325e056a820009c3d52752a9d994423a48/re/solidworks/measurements/2026/SdkOrdinaryPartDefinition01.json) Scoped Black, repository steering and Mypy checks passed for all 28 source paths. The recorded-payload scan passed across `src`.

```sh
python3.14 -I -B re/tooling/sw2026/definition/ProveOrdinaryPartDef.py
```

Run the proof with the scoped changes on the pinned base and both historical Git objects available. The proof measures the internal stream codec. Standalone file generation, public writer admission and fresh native or held-out lifecycle evidence have separate exits.
