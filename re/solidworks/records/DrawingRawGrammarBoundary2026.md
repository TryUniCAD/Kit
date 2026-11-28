# Raw drawing grammar and semantic admission in SOLIDWORKS 2026

Both exact original Definition streams now round-trip byte identically through the shared SDK field grammar, with zero tail and preserved maps/object identities. Both normal named-drawing reads still reject the unchanged UI-state guard. This is a raw-codec instrument result, not complete drawing semantics, a generated original, public admission, or native/held-out writer acceptance.

Task: PR121 disclosed drawing raw-grammar boundary. Owner: `flag_ownership`; delivery PR: #121. Dependency: [the BOM-manager reader](DrawingBomManagerArchive2026.md). Exit: frozen independent tool, exact source/custody checks, complete raw read/store and map comparison, and preservation of the original normal-reader rejection. Remaining UI and source-semantic work stays explicit.

## Why a separate instrument

The normal `ReadNamedDef` finishes `ReadBodyMut`, checks that the cursor has no remaining bytes, derives runtime containment aliases, and then applies graph/UI qualification. After the manager dependency was linked, both actual originals stopped at `blank drawing Definition has unqualified ui state`. The existing ordinary probe therefore never emitted those graphs and established no byte identity.

The new [research inspector](../../tooling/sw2026/InspectDrawingRawDefinition.py) uses the same existing SDK `BinaryReader`, `GraphReader`, version-19000 `BodyContext`, field layouts, schemas, virtual dispatch, and base-one archive maps. It reads the shared prefix and exact drawing CLSID, executes the ordinary body grammar, requires zero remaining bytes, and reuses the existing containment binder. It stores the resulting typed graph through the same field executor and inline-header writer.

For the raw sheet path it executes the existing declared model-feature base and sheet field layout directly, rather than claiming the narrower sheet/UI semantic validators passed. It does not patch or disable any SDK guard, alter a layout, add an API mode, or replace a source field. The unchanged normal `ReadNamedDef` is independently called on the same bytes, and its exact known rejection is required for this bounded raw-only result. The tool saves no CAD file or Definition payload.

## Frozen custody and results

The source candidate contains 4,351 files and is bound by manifest SHA-256 `b89ea3132b84887218a1a2ed6fca7f0e397d7a03b744a663d97a3b1ce4b962b5`. The inspector SHA-256 is `2255de925dceb557a5111cd1efc4c1f408e1aec18f2e6582b0002ff001952c4c`. Both exact already-disclosed Run02 drawing hashes are allowlisted. The access manifest and every code file's size/hash are checked before and after measurement; output must be unused.

Root independently executed the inspector. Private raw result SHA-256 is `4cded03acba32e3aa58f859bcb23c3b4f120cd993642078b518b569de81194f3`. The [sanitized receipt](../measurements/2026/DrawingRawGrammar01.json) retains source/output hashes, complete schema inventories, usage counts, field ownership/length metadata, maps, UI guard selectors, and the unchanged normal failures. Packed scalar value arrays remain in the private raw report rather than the published summary; their field/count/length owners remain visible.

| Exact original | Definition bytes | Input and output SHA-256                                           | Load/store used schemas | Map next / entries | Tail |
| -------------- | ---------------: | ------------------------------------------------------------------ | ----------------------: | ------------------ | ---: |
| H01SheetA      |           37,612 | `f3f6a00cdb39c81eb00384ed8b680b89a8bc6a965cf83e08a6b0ebdac8868ca2` |               215 / 215 | 331 / 330          |    0 |
| H02SheetB      |           37,608 | `2d10ff1e4e2558a8af0910176c551e1236c4f98d94601539718867d82036646f` |               215 / 215 | 331 / 330          |    0 |

Each direction records 1,277 schema calls, 7,951 field calls, and three explicit native byte fields. Missing and provisional schema inventories are empty. Complete map slots match and every mapped object remains the same actual graph object through store. Inputs and source code remain immutable.

Both decoded `has_pwmaterial` selectors are one; both `drawing_end_marker` values are 3503. The existing normal guard requires presence zero and end marker 3503, so the observed marker already satisfies that part of the guard. These are source observations, not construction defaults or proof of the preceding material/marker semantics.

## Usage

Use an exact frozen reader candidate and the existing hash-bound source-access manifest. Choose an unused metadata output path.

```text
python -I -B re/tooling/sw2026/InspectDrawingRawDefinition.py \
  /path/to/frozen-reader /path/to/SourceAccess.json /unused/RawDefinition.json \
  --manifest-sha256 <frozen-reader-manifest-sha256> \
  --access-sha256 <approved-source-access-manifest-sha256>
```

Exit zero means both exact raw comparisons and map checks passed while both specified normal semantic rejections remained. Exit three retains raw failure/phase, usage and cursor diagnostics. The command never treats a normal read rejection as public success. It is bounded to these already-disclosed originals and does not accept arbitrary sealed sources.

## Limits and next proof

The worker performed AST and formatting checks only; the actual SDK process was executed independently by root. No SDK implementation, original frozen writer, normal guard, CAD application, VM, service, or license state changed. This measurement covers Definition only, not Header2, container byte identity, complete neutral projection, tree/link equivalence, or fresh construction.

Actual material-presence and preceding marker ownership require native proof before any semantic guard extension. Original source tree/link differences and the failed complete-source verdict remain retained. See [the raw-parity admission gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/Qualification/RawDrawingParityLeavesUiAdmissionClosed.md) and the [machine-readable boundary record](DrawingRawGrammarBoundary2026.json).

The mandatory stopping conditions remain “The first is success under every criterion on this page.” and “The second is the end of the available context.” A successful byte instrument does not end the CAD goal.
