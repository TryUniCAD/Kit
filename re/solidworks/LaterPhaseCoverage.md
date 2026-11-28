# Later-phase offline coverage

This audit follows the plan on PR #296. It measures the checked-in reader and
conversion gates, not complete CAD support. No SOLIDWORKS, Fusion, FreeCAD or
CATIA application was used. No schema or adapter behavior changed.

## Inventory and coverage

On base `1619f00bf`, the case-sensitive tracked-file inventory
(`git ls-files -z '*.SLDASM' '*.SLDDRW' '*.SLDPRT'`, counted by suffix with
NUL delimiters) returned:

```text
{'SLDASM': 6, 'SLDPRT': 322}
```

No tracked uppercase `.SLDDRW` matched. The assemblies are all from the
`Single Turbo Dual Overhead Cam V8 - KDP - 2024` example family. Part counts
include controls, variations and other research cases; they are not coverage
counts or proof of independent holdouts.

| Phase | Offline decode and interchange | Offline convert | Compared with FreeCAD / CATIA |
| --- | --- | --- | --- |
| Compound parts | `Piston Ring KF.SLDPRT` exposes one body, a timeline of 28 entries, sketches, parameters and native payloads. This is a dependent-feature example, not a qualified multibody case. The interchange model has bodies, feature references and B-rep payloads. | The tested part refused JSON, FCStd and CATPart export at the native-feature gate; no general patterns, mirrors or multibody conversion follows from the decode. | FreeCAD: `ambiguous`; CATIA: `different`. B-rep and retained payloads are outside graph qualification. |
| Document state | `CircularProperties.SLDPRT` exposes active `modeled default`, distinct document and configuration text properties, and no material records. Interchange has configurations, overrides, suppression, metadata and materials; presence of these types is not a measurement of import or write support. | JSON, FCStd and CATPart export hit the native-feature gate. FreeCAD's format table marks configurations target-unsupported; a CATIA carrier is not proof of native state publication. | FreeCAD: `ambiguous`; CATIA: `different`. Configuration/material records can enter the graph; metadata and unclassified extension fields are not semantic parity evidence. |
| Assemblies | `Cylinder Head Assy 1.SLDASM` exposes 12 definitions, 5 component documents, 119 instances, 480 mate entities and 240 mates. The interchange assembly also models transforms, mate groups and component references. Counts do not establish complete resolution or solver behavior. | JSON, FCStd and CATProduct refused at the native-feature gate for this fixture. `.SLDASM` is a recognized source suffix, not a writer suffix. FreeCAD and CATIA have assembly routes, which does not establish this source is accepted. | Both attempts: `comparison JSON exceeds its structural limit`. Even for a smaller input, the graph marks assembly as a domain requiring independent comparison. |
| Drawings / compatibility | No matching fixture or SOLIDWORKS drawing reader in `kit formats`. A synthetic empty file with that suffix failed dispatch; it is not a drawing fixture. The generic interchange document has no drawing sheet/view model. | No SOLIDWORKS drawing route established. A reader/writer extension list does not establish vendor-version support. | No drawing document to compare and no drawing domain in the semantic graph. |

## Reproduce the boundary

Run `kit formats`, then `kit decode SOURCE -o inspection.json` and
`kit convert SOURCE TARGET --json` with the samples and target suffixes above.
Use `kit decode SOURCE --configuration 'modeled default'` on the property
fixture to inspect the two property scopes. The existing SDK integration
records the authored property values in
[LiteralTextTests.py](../../tests/Convert/Solidworks/Properties/LiteralTextTests.py);
the new process-level check pins the same distinct revision values through
explicit configuration selection in the CLI decode envelope.

Representative refusal messages (verbatim):

```text
NativeFeature records are not conversion-ready; use kit decode or kit research for inspection
no writer supports the destination suffix; use --to FORMAT
no reader recognizes the source
comparison JSON exceeds its structural limit
```

For the comparison probes, decode the committed
`re/FreeCad/Verification/AliasEqual.FCStd` and
`re/catia/examples/.CATPart/Bolt_M5x40.CATPart` alongside the SOLIDWORKS
inputs. Extract the `document` object from each decode envelope as a separate
JSON file, hash those exact bytes, and pass them through
`SemanticComparison.document_input` and `compare_documents` (or the script's
hash-pinned CLI). The diagnostic run used declared millimetres for both
inputs, zero absolute tolerance for each quantity, and the default
candidate budget. These are unrelated controls, not matched or newly
converted models. The outcomes above exercise ingestion and show the
boundary; they do not establish discrepancies between equivalent designs.
All returned reports stated `native_acceptance: not_established`.

`SemanticGraph.py` walks selected records such as configurations, bodies,
materials and feature references. It explicitly leaves assembly, B-rep,
payloads, diagnostics and metadata to independent checks. Assembly graph,
property scopes and drawing associativity need their own oracle checks even
if a narrower graph match reports equality. The [capture backlog](CaptureBacklog.md)
lists the controls needed before expanding any support claim.
