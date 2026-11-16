# Verify archive usage summaries against complete phases

The curve source process checker previously passed a file-level usage summary
to the individual-phase assertion. Aggregate summaries contain schema-name
unions and raw-operation counts; they do not have a `completed` field. After
the final provisional map owner was grounded, both archive CLI commands reached
that assertion and their process checks failed with `KeyError: completed`.

The focused `AssertSummary` helper now verifies the aggregate's actual contract.
It reconstructs each direction's schema union and raw-operation count from all
selected stream and linked-dependency snapshots. Every actual phase must still
be complete and have no used provisional or missing schema. Existing stream,
seed, hash, tail and byte-identity assertions remain active. The codec, schema
usage API, strict admission rules, CLI arguments and timeouts are unchanged.

The [remote process job](https://github.com/TryUniCAD/Kit/actions/runs/43805235770/job/133094377267)
for source `b291c4da06406d61059b6a0095d3bbb825ef7ef1`
reported 179 passing cases, 158 fixture-dependent skips and exactly these two
aggregate-consumer failures. All field-inventory process cases passed in that
job. Raw archive metadata and graph admission are audited separately; this entry
does not infer a new-revision result from those earlier reports.

Verification of this repair is static AST, source, link and formatting review
only. No tests, collection, schemas or codecs ran locally. Fresh remote process
and quality checks remain pending. This is source-report validation and adds no
generated curve writer, held-out model acceptance or production write capability.

See the [schema-usage contract](SolidworksArchiveSchemaUsage.md),
[field-inventory process checks](SolidworksCurveFieldInventory.md),
[aggregate-scope gotcha](../../../Gotchas/Conversion/Solidworks/Archive/AggregateUsageIsNotAPhaseSnapshot.md)
and [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md).
