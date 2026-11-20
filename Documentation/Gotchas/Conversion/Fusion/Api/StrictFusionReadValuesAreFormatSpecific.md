# Strict Fusion read values are format-specific

`ReadOptions.values` is interpreted by the selected adapter. The strict
Fusion reader permits only `fusion.inflate_zstd` in this map. A generic
marker in the map causes a qualification error before source bytes are read.

The public `extract_brep` operation uses the separate typed
`ReadOptions.raw_brep_only` field for its read intent.
SOLIDWORKS uses that field at its local reconstruction boundary.
Fusion keeps its normal strict read and returns an empty extraction
when the archive has no detachable B-rep payloads.

[Strict Fusion reader](../../../../../src/convert/adapters/Fusion/Bridge/ReadStrict.py)
· [Public extraction control](../../../../../tests/Convert/Api/Fusion/RawBrepTests.py)
