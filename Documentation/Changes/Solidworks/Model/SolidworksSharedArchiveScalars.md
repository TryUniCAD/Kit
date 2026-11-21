# Share fixed-width SOLIDWORKS archive scalar I/O

The SDK archive layer now owns the fixed-width integer and floating codecs used
by the research linked loader and the SDK header field codec. The ordinary
Config, CMgr, ResolvedFeatures and Mates paths call the shared implementation
through their existing primitive entry points. Their field layouts and context
rules retain their existing ownership.

`ReadScalar` returns the number and next position after a complete field.
`EncodeScalar` returns bytes after the existing numeric conversion and range
checks succeed. The ten declared kinds cover signed and unsigned 8/16/32/64-bit
integers and IEEE binary32/binary64, with explicit little-endian representation.
Generic boolean and numeric-protocol conversions keep their prior behavior.
The SDK header retains its stricter integer-field validation. Short reads and
failed packing retain the cursor and output-buffer state required by their callers.

The source census identifies 299 reached schemas across 32 research modules in
twelve disclosed/generated files. It records the independent CMgr context map,
the Config-to-Resolved-to-Mates identity chain and per-phase proof status. The
remaining provisional dependencies are `su_CMapStringToString` in Config and
`moContextChainComponent_c` in CMgr/Resolved. Public semantic graph admission
still requires their qualification and the remaining production body grammars.

Five relevant process integrations passed locally. Two malformed generated
containers fail at their actual scalar read boundaries through the normal CLI.
Twelve files passed the linked graph comparisons, all six prior typed mate CLI
outputs stayed byte-identical, and a generated child's strict linked inventory
verified 92 source fingerprints. Scoped Black, Ruff, Mypy, Pyright and steering
checks passed. Native application and held-out acceptance require their separate
evidence.

[Representation rules and concrete dependency census](../../../../re/solidworks/records/LinkedGraphScalarConstruction2026.md)

[Process and source receipt](../../../../re/solidworks/measurements/2026/LinkedGraphScalarCensus01.json)
