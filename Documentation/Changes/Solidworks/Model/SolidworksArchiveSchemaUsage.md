# Archive schema usage reporting

The research round-trip checker now records the schemas that each stream operation executes.
Load and store evidence remain separate.
The report distinguishes byte identity from admission through registered, nonprovisional schemas.

## Usage

Run the checker in remote CI or the authorized research verification job.
The example paths are placeholders, not observed inputs or results.

```sh
uv run --no-sync python re/tooling/sw2026/serial/RoundTrip.py '/tmp/CurveDiscoveryCorpus/*.SLDPRT' --require-proven --report /tmp/CurveSchemaUsage.json
```

Add `--link-config` to check the existing configuration-map handoff.
The selected resolved stream retains its own byte comparison.
Its linked configuration load appears separately under `schema_usage.dependencies`.
The dependency record contains its source byte count, SHA-256, unread-tail length and schema usage.
It does not claim an additional byte comparison.

Without `--require-proven`, the existing byte-identity and unread-tail success conditions remain unchanged.
With the flag, a stream also fails when its operation or linked dependency uses provisional schemas or attempts missing schemas.
Unused provisional declarations do not fail this check.
Existing missing-schema, unread-tail, byte-difference and missing-input failures remain failures.

## Report fields

| Location | Meaning |
| --- | --- |
| Top-level `provisional_schemas` | Existing complete registry inventory, including unused declarations |
| Top-level `used_provisional_schemas` | Provisional names reached in this invocation |
| Top-level `require_proven` | Whether the additional admission check was requested |
| Top-level and file `byte_identity_passed` | All selected stream comparisons passed the existing byte and tail conditions |
| Top-level and file `proven_schemas` | Every selected operation and dependency completed without errors, tails, provisional schemas or missing schemas |
| File `schema_usage.load` and `.store` | Separate unions for that file, including dependency reads, with raw-operation counts |
| Stream `byte_identity_passed` | Existing stream byte comparison and unread-tail result, before the optional admission check |
| Stream `proven_schemas` | Its complete load, store and linked-dependency admission result |
| Stream `schema_usage.load` and `.store` | Actual schema names, declaration status, call contexts and reached raw operations |
| Stream `schema_usage.dependencies` | Separate linked-map seed load snapshots, including byte/hash/tail metadata |

The existing stream byte count, SHA-256, root count, tail count, equality result and map fields remain available.
`passed` includes the additional admission condition only when requested.
A failed load or store preserves the usage collected before its exception.
An unstarted phase has a null snapshot.
Each started phase records `completed`, which stays false when its context exits through an exception.
Framing errors, incomplete operations and unread tails make `proven_schemas` false even when no schema names were collected.
A missing required stream remains a failure and has no executed-schema claim.

## Dispatch and source context

The registry records actual schema execution, including zero-operation schemas.
A class tag or object reference alone does not execute a schema body.
Missing schema attempts are reported separately from executed schema names.
`missing_schemas` records named schema attempts that reach the registry.
Malformed tags, invalid references and unresolved external or virtual dispatch can fail before a schema name reaches this boundary.
Their missing inventory can remain empty, while the phase remains incomplete and `proven_schemas` remains false.
Registry capability queries do not count as execution or missing-schema attempts.

`schema_calls` reports the schema, parent schema, concrete object class, source candidates, call count and entry route.
Routes distinguish tagged objects, base calls, embedded calls and direct calls from custom framing or dispatch operations.
The tracker retains the owning schema when an operation enters nested or repeated scopes.
Tagged archive objects provide `object_class` metadata.
Other valid direct contexts, including null or mapping contexts, record a null `object_class` and their Python `object_type`.
This metadata does not replace the context passed to the schema or suppress its own errors.

Custom loaders can read prerequisite streams internally.
Their schema calls identify input buffers through archive byte identity, then byte equality when needed.
`source_streams` contains all matching candidates when the buffer is ambiguous.
An empty list identifies an unmatched input buffer.
Store entries identify the requested output stream.
These usage entries do not confer an independent byte-comparison result on a prerequisite stream.

Each load, store and linked-seed phase receives a new usage context.
Nested contexts restore their previous context in `finally` blocks.
Per-file summaries use only that file's completed or partial stream records.
The CLI uses one registry sequentially, but usage does not accumulate across fixtures.
Concurrent operations sharing one registry are outside this instrumentation's scope.

## Raw byte operations

Every reached `Raw` operation reports its owning schema, concrete object class, field and nested operation path.
The record includes its constant or callable length rule, declared length, observed byte count and completion state.
Callable rules identify their module, function, source file and line from the in-memory callable.
The report never reads source files during archive execution.
`source` remains null and `source_status` states that boundary.
Use the referenced independently authored schema definition to inspect its formula.
The recorder does not invoke the length callable a second time.

This includes native byte-array schemas implemented with `Raw`, such as `su_CByteArray` and counted native arrays.
It also exposes reached GUID and Parasolid byte fields under their existing schema owners.
An incomplete raw operation reports the bytes actually consumed or emitted before failure.
CString and class-tag encoding remain the responsibility of the existing archive core.
This list is an inventory of schema `Raw` operations, not every low-level byte transfer.

Raw operations, parameter records and unread tails retain their existing serialization behavior.
The change introduces no schema fields, defaults, archive plans or fallback bytes.
No production module imports this instrumentation.

## Limits and verification

A nonprovisional declaration can still have unresolved semantics or missing branches.
`--require-proven` enforces registry declaration status, not complete CAD acceptance or generative-writer correctness.
The [gotcha](../../../Gotchas/Conversion/Solidworks/Archive/ProvisionalSchemasDoNotProveClosure.md) explains this distinction.

Static inspection confirmed dispatch through the shared registry and preserved stream plans.
The caller audit found that current custom entry points construct or forward tagged archive objects.
The generic dispatch instrumentation also permits direct schemas whose operations do not require a tagged object context.
Both draft Python files passed AST parsing.
No schema module, CAD file, corpus fixture or local test was executed during this change.
The [first remote process run](https://github.com/TryUniCAD/Kit/actions/runs/43784683947/job/133029564572)
on `6047d1d5594210cdfbe13b2c3aea45e5105b866f` passed the existing source-archive round trips
but failed two fresh-construction checks: callable source inspection attempted eight
reads of `ResolvedDims.py` inside each guarded construction process.
The [source-inspection gotcha](../../../Gotchas/Conversion/Solidworks/Archive/SourceInspectionCanReadDuringConstruction.md)
records the cause and repair. Removing source retrieval preserves those read-denial assertions.
Fresh construction and full remote verification of the repair remain pending.
No native load, rebuild, edit, geometry or writer acceptance is claimed.

The [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) retain both stopping conditions:

> The first is success under every criterion on this page.
> The second is the end of the available context.

See the [schema guide](../../../../re/tooling/sw2026/serial/README.md),
[registry implementation](../../../../re/tooling/sw2026/serial/Schema.py)
and [round-trip checker](../../../../re/tooling/sw2026/serial/RoundTrip.py).
