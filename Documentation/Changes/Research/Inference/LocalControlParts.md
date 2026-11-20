# Local control parts for file-driven decoding

The SOLIDWORKS field-discovery and extrusion-depth experiments now search tracked paired captures and versioned corpus parts alongside the examples. Supply additional local saves with one `--control` per file, for example:

```sh
kit run solidworks --input wheel.SLDPRT --control pattern-90.SLDPRT --control pattern-180.SLDPRT --directory wheel-evidence
```

Each supplied control must have native part metadata, one configuration and resolved feature records. Input and control resolved streams must be distinct. The run accepts up to 32 additional files, at most 16 MiB per file and 64 MiB in total. It hashes and snapshots them in the private scratch directory before analysis. Every successive reader pass uses the same snapshots. The file-scope report records their hashes and qualifying training samples carry their own file and stream hashes.

The local wheel run used the cover as an explicit control. Its resolved stream also exists in the tracked corpus, so its observations counted once. The unresolved circular-pattern sweep still requires independent variation of the declared angle. Supplying controls can distinguish a hypothesis only when their native measurements differ in the relevant field.
