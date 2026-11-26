# Inferring a reader from raw scalar streams

The automatic file command searches an unidentified binary containing native SOLIDWORKS name markers for a numeric layout. The existing marker identifies the start of a length-prefixed name. The search uses registered discovery saves with recorded parameter edits and clean native reopen measurements. It compares four floating-point representations and 97 displacements after the name. When exactly one candidate survives, it retains the header positions shared by the examples and generates a Python reader. The format, displacement and fixed header positions are inferred before the qualification and holdout comparisons.

The generated reader runs as a separate process on the supplied stream and the measured streams. All qualifying trials must reproduce the named measurements at the corresponding byte positions before the CLI publishes a research patch. The inference and its validation reuse the repository's existing capture measurements. Neither requires a CAD installation. Values carry their stored units. A parameter name ending in `_deg` can still have a scalar in radians.

```sh
kit run --root . auto --input edited.bin --control baseline.bin --directory /tmp/raw-scalar-run
```

The P05 90° revolution stream recovered four measured values: inner radius 0.002 m, outer radius 0.006 m, height 0.012 m and angle π/2 radians. The independent baseline encoded 2π radians. The runner attributed 32 bytes of the 17,744-byte input to these four measured scalars. The remaining bytes and the larger feature semantics remain unresolved. See `Input-raw-structure.json` for source hashes, evidence roles and values, and `Reader.patch` for the generated parser.

For generic length-prefix hypotheses, `--control` reports which candidate layouts also consume the comparison bytes exactly. User-supplied controls challenge candidate layouts and are excluded from scalar fitting when their stream hashes match. A shared layout alone is insufficient to promote a reader. Well-formed UTF-8 XML is inspected as markup before running the binary experiments.


A full SOLIDWORKS part also enters this experiment automatically. For a part run the output is `NamedScalarReader.patch`; the receipt identifies every configuration member replayed through the generated program's native-container entry point. Apply it on the receipt's base commit and run `PYTHONPATH=src:re/automation python re/solidworks/DerivedReaders/NamedScalarReader.py part.SLDPRT --member Contents/Config-0-ResolvedFeatures`. The archive scan admits eight configuration members and 32 MiB per run. The evidence lists deferred members. Native archive and matching configuration stream hashes are excluded from discovery fitting.
