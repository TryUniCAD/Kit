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

The process checks in `tests/convert/solidworks/research/` require exact re-emission
of every critical stream for all eight controls. Tests run in remote CI only.
No local test execution or new vendor acceptance is claimed by this entry.
Remote checks remain pending until the PR reports them.

Assembly schemas, complete field classification, synthesis from a neutral document,
held-out measurements, and production conversion remain unfinished.
The [adapter guide](../../Reference/Adapters/Solidworks.md) retains that boundary.
