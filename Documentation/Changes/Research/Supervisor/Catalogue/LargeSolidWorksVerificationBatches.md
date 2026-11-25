# Larger SOLIDWORKS verification batches

New SOLIDWORKS authoring runs group up to twelve configured cases in one
native batch. One owned process authors the cases. A different owned process
reopens, rebuilds and measures every required archive. The verifier closes
each case's documents before starting the next case.

Run the existing `kit run solidworks` catalogue command with authoring
enabled. No new option is required. The plan records
`solidworks_batch_size: 12`. Saved plans without that field keep their
three-case partitions and original job identities. The actual file count
depends on each case's baseline, edits and variants. At 26 to 27 archives
per three cases, twelve cases would produce about 104 to 108 archives.

The supervisor scales the default native phase and capture-job deadlines in
three-case increments. An explicit `phase_seconds` in the SOLIDWORKS host
configuration remains the per-phase limit. Each case keeps its own bundle
and decoder job. The existing per-batch artifact budgets and native acceptance
checks continue to apply. A native phase failure can still block the entire
batch before its files are released to the decoder.

Process checks cover complete twelve-case groups, the final partial group,
saved jobs from the previous implementations, per-case artifact routing, and
the native manifest at its upper bound. Licensed acceptance requires both
owned process exits, successful reopen and rebuild of every file, and
unchanged archive hashes. See
[A08h-LargeSolidWorksBatches](../../../../Reference/Research/AutomationSteps.md#a08h-largesolidworksbatches-larger-fresh-verification-groups).
