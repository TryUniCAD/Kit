# SOLIDWORKS 2026 archive research

## Behavior

The research tools model SOLIDWORKS 2026 SP05.2 archive records.
They include oracle authoring and measurement scripts, a regenerated class map,
stream schemas, and a command that checks object-level byte identity.
All tools stay under `re/`. Kit still reads SOLIDWORKS files and cannot write them.

The checker rejects missing input files, missing requested streams, unsupported
versions, schema failures, unread bytes, and byte differences.
Its JSON report records file hashes, stream hashes, map counts, and provisional schemas.
Configuration streams use their own model headers through an explicit archive context.
Wire values and loader fixups are distinct where a scalar is normalized on load.

## Use

Run the following command in remote PR CI:

```sh
uv run python re/tooling/sw2026/serial/RoundTrip.py 're/solidworks/v2026/corpus/ladder/*.SLDPRT' --report archive-report.json -v
```

Supply a second positional argument to require a comma-separated stream list.
The default requires the seven streams identified by individual deletion experiments,
then checks other modelled streams that are present.
See the [research guide](../../../re/tooling/sw2026/serial/README.md) for details.

## Evidence and limits

The [binary manifest](../../../re/solidworks/v2026/Manifest2026.json) binds the
2026 binary evidence to version `34.5.2.0604`.
The [class-map comparison](../../../re/solidworks/v2026/SerializeMapDiff.md) records
the version differences.
The [fixture manifest](../../../re/solidworks/v2026/corpus/ladder/Manifest.json)
records eight authoring specifications, source measurements and hashes.
Personal metadata in the fixtures is redacted at the same encoded width.
Those fixtures are research inputs and are not generated writer output.

The process checks in `tests/Convert/Solidworks/Research/` require exact re-emission
of every critical stream for all eight controls. Tests run in remote CI only.
No local test execution or new vendor acceptance is claimed by this entry.
The [initial remote measurement](../../../re/solidworks/measurements/ArchiveRoundTrip2026.md)
recorded 48 of 56 exact critical-stream re-emissions.
All eight configuration streams failed with a four-byte section deficit.
After the missing typed array and empty-collection repairs, head
`8eb76d2b87b5a400f23360a7623a66cc773bc389` passed all 56 required stream
round trips in the [remote native-file job](https://github.com/TryUniCAD/Kit/actions/runs/43661634387/job/132652029522).

The [wire-state field table](../../../re/solidworks/records/ArchiveWireState2026.md)
records the binary evidence and unresolved classification questions.
The [header](../../../re/solidworks/records/HeaderConstruction2026.md) and
[history](../../../re/solidworks/records/HistoryConstruction2026.md) studies add
constructor-derived rules without promoting them as accepted writer defaults.
The [polygon ledger](../../../re/solidworks/records/PolygonConstruction2026.md)
records variable-topology construction rules and the remaining builder obligations.

Oracle helpers now record failed feature queries and cleanup operations.
Failure to set construction geometry or select system mass-property units is no
longer silently ignored. These scripts still need remote target acceptance.
The disassembler uses structured memory operands and explicit PE symbol budgets.

Assembly schemas, complete field classification, synthesis from a neutral document,
held-out measurements, and production conversion remain unfinished.
The [adapter guide](../../Reference/Adapters/Solidworks.md) retains that boundary.
