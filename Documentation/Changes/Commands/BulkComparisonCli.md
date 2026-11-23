# Bulk comparison through Kit CLI

```sh
kit research --root . compare SolidWorks Fusion --unit mm -o Comparison
kit research --root . compare --manifest Pairs.json --unit mm -o Comparison
```

Use a new output directory for each run and the geometry unit declared by the export source.
For different geometry units, supply `--left-unit` and `--right-unit` in place of `--unit`.
The command refuses omitted unit declarations and conflicting pairing or unit options.
Existing direct comparator scripts retain their directory flags, per-side unit options and `--output`.

The installed command writes `Comparison/unified/` alongside its reports.
For each exact observed match with no unresolved issues, it copies the original left JSON bytes after checking their comparison digest.
Summary rows record the artifact path, side, digest, byte count and declared unit.
Nonzero tolerances disable unified copying. Every pair still receives its detailed comparison report.
Copies use the existing bounded batch budget and a new output directory. If a copy fails, its row records the failure and the batch exits with status `1`.
Existing direct invocations can opt in with `--unified`.

The installed CLI selects the existing comparison script from the trusted checkout identified by `--root`.
It preserves the comparator's reports, input evidence and output refusal.
A checkout that predates unified publication reports the missing capability.
Comparison reads existing neutral JSON and leaves decoders and CAD applications idle.
See the [comparison guide](../../Tasks/CompareDecodedDocuments.md).

Installed-command process coverage exercises folder and manifest pairing, reports and exit status, unified copy provenance and skipped copies, shared and per-side units, option collisions, help and an older checkout.
Remote process verification is pending on this revision.
