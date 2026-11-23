# Bulk comparison through Kit CLI

```sh
kit research --root . compare SolidWorks Fusion --unit mm -o Comparison
kit research --root . compare --manifest Pairs.json --unit mm -o Comparison
```

Use a new output directory for each run and the geometry unit declared by the export source.
For different geometry units, supply `--left-unit` and `--right-unit` in place of `--unit`.
The command refuses omitted unit declarations and conflicting pairing or unit options.
Existing direct comparator scripts retain their directory flags, per-side unit options and `--output`.

The installed CLI selects the existing comparison script from the trusted checkout identified by `--root`.
It preserves the comparator's reports, input evidence, output refusal and exit status.
A checkout that predates the comparator reports the missing tool.
Comparison reads existing neutral JSON and leaves decoders and CAD applications idle.
See the [comparison guide](../../Tasks/CompareDecodedDocuments.md).

Installed-command process coverage exercises folder and manifest pairing, reports and exit status, shared and per-side units, option collisions, help and an older checkout.
Remote process verification is pending on this revision.
