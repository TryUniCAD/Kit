# Complete decoded field inventory for curve correlation

`FieldScan.py --inventory-json` adds a complete decoded-value graph for remote discovery correlation.
The existing text and `--json` summaries keep their previous output and six-value limit.
The new mode does not write CAD files or infer construction rules.

## Remote use

Run this tool only in authorized remote CI after the discovery corpus passes its archive round trips.
Select the prepared discovery/control corpus, with its manifest and source-lock hashes verified separately.
Keep held-out native payloads outside the selected pattern.
Create the report's parent directory and select a new report filename.

```sh
uv run --no-sync python re/tooling/sw2026/serial/FieldScan.py \
  're/solidworks/v2026/corpus/curves-discovery/*.SLDPRT' \
  Contents/Config-0-ResolvedFeatures \
  --inventory-json /tmp/CurveResolvedFields.json --link-config --require-proven
```

This example has not been executed for this change.
The process writes one JSON report and prints a compact receipt.
Exit zero requires at least one input and successful inventory of every selected file.
Existing report files and symlink inputs are rejected.
The legacy `--json` summary and new inventory mode are separate interfaces.

Use `--require-proven` to reject provisional or missing schemas reached during load and explicit dependencies.
`--link-config` requires a custom resolved-features plan.
It loads the corresponding configuration and passes its actual map into the resolved loader.
Other streams use their normal archive context without that option.
Run separate inventories for the other critical/header streams.

## Report contract

The report schema is `kit.sw2026.field-inventory.v1`.
Each file records its exact input hash, size and selected decompressed stream hash.
It also records schema usage, failure stage, explicit dependencies and implementation-source hashes.

| Representation | Recorded information |
| --- | --- |
| Integer | Exact JSON integer and an authoritative decimal string |
| Float | Decoded value, finite status, hexadecimal numeric representation and decoded Python binary64 bits |
| String or boolean | Complete decoded value and owner/path context |
| Byte field | Length and SHA-256 only, with no hexadecimal, base64 or raw payload dump |
| List or tuple | Every item, its index and the complete length |
| Dictionary | Every ordered key/value entry with typed keys |
| Object | Class, schema, captured archive index, record boundaries, fields and origin stream |
| Reference | Explicit report-local target identity and referencing owner/path context |
| External reference | Actual archive index, explicit unresolved state and referencing context |

Graph nodes receive deterministic encounter-order identities within each file report.
Objects and containers are retained while assigning identities, so temporary Python identities cannot be reused.
Shared references and cycles point to the same graph node.
Class-map entries retain their original tagged tuples, so seeded class metadata
shares its retained tuple identity instead of acquiring a synthesized slice identity.
These identifiers are analysis labels, not persistent feature IDs or writer object-map indices.

`decoded_python_binary64_be` preserves the current Python float's sign and payload,
including NaNs that share the same `float.hex()` text.
This is a decoded Python binary64 representation. It does not claim that the native
field was f64 or that a native f32 NaN payload survived the codec's conversion.

The graph contains retained document headers, roots, loader context and archive-map entries.
Linked mode also includes the complete retained configuration graph and its source hash.
Seeded objects retain their configuration origin when referenced by the resolved graph.

Custom loaders can read additional manager or model-header context.
`loader_source_streams` lists those observed source candidates, with hashes and explicit `graph_included` flags.
An auxiliary source marked false needs its own selected-stream inventory.
The report does not claim to recover discarded local variables or independently trace every primitive read.

Failure records contain exception type and a hash of its message.
They do not serialize arbitrary codec exception representations that could contain opaque bytes.
Schema usage remains available for archive-load failures after tracking begins.
Failed files do not receive successful correlation credit.

## Verification

The change adds fourteen focused process-suite modules under
`tests/convert/solidworks/research/Curve/Fields`.
Nine fresh CLI processes select the eight critical/header streams and the separate
linked resolved stream across all 26 prepared inputs, producing 234 inventories.
Three negative processes select an empty pattern, a missing stream and a truncated
copy of a real fixture. Every invocation retains `--require-proven` and the existing
120-second process timeout.

Source inspection, AST parsing and formatting checks were performed locally.
The tool, archive codecs, schemas and tests were not executed locally; remote
process results remain pending. The suite checks:

1. Verify the exact 26 prepared discovery/control files against their manifest and portable source lock.
2. Invoke the real `FieldScan.py` process for each intended critical/header stream.
3. Invoke linked resolved mode separately and require the configuration dependency hash, zero tail and map handoff.
4. Require exit zero, report success, complete load usage and no used provisional or missing schemas.
5. Match every report file and selected stream hash/length against the prepared manifest.
6. Require unique node IDs and a valid target for every internal reference.
7. Require every list/tuple item and dictionary entry to match its declared length, including elements beyond index five.
8. Require authoritative integer decimal text to equal the exact parsed integer, including values beyond JavaScript precision.
9. Check byte-field records for length/hash metadata and absence of payload encodings.
10. Preserve unresolved references explicitly; never invent a target from matching class names or coordinates.
11. Exercise an empty pattern, missing stream and truncated native fixture through the same process boundary.
12. Require nonzero exit and structured failure evidence for every negative case.
13. Retain inventory JSON, stdout, stderr and exact CI/head/source provenance as discovery instruments.

These checks belong at the actual CLI/file boundary, not in unit tests or fabricated object graphs.
The existing native-file workflow discovers the process modules under the SOLIDWORKS test tree.
It retains report JSON, stdout, stderr, scope receipts and observed value-kind counts
under `SourceParser/Curve/Fields`, including failure evidence when the process exits nonzero.
Legacy summary function bodies were compared statically with their previous revision;
no legacy CLI execution is claimed by this change.
This change does not add a workflow or modify `RoundTrip.py` or `Schema.py`.

## Evidence limits

The type tags describe decoded Python values.
They do not infer native scalar widths, field byte offsets, legal domains or authored/derived classifications.
Object boundaries are recorded only when the existing loader captured them.
Native byte fields remain semantically unclassified even when their length and hash are known.
Inventory completion is separate from byte identity, loader acceptance and native writer acceptance.

Correlate these values with source specifications and pinned native-loader evidence.
Do not promote observed values, invariant rows or fitted formulas into writer defaults.
Fresh curve generation and held-out native measurements remain the goal.

The [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) state:
“The first is success under every criterion on this page.”
They also state: “The second is the end of the available context.”
This inventory does not close that goal.

See the [summary limitation](../../../Gotchas/Conversion/Solidworks/Archive/FieldSummariesDoNotInventoryValues.md),
[correlation method](../../../../re/Playbook/CorpusCorrelation.md),
[archive map finding](../../../../re/solidworks/records/ArchiveMapConstruction2026.md),
and [schema usage limits](../../../Gotchas/Conversion/Solidworks/Archive/ProvisionalSchemasDoNotProveClosure.md).
