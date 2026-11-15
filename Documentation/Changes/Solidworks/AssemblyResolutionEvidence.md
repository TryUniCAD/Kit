# Explicit SOLIDWORKS assembly source evidence

SOLIDWORKS assembly component definitions now include the boolean attribute
`source_resolved`. It is true for the root definition decoded from the assembly
and for a component whose document was actually loaded. It is false for every
other unloaded component, including components with cached display meshes.

`source_path` remains provenance. A cached mesh, source filename, or local
instance graph does not prove that an external component document was loaded.
The attribute also records missing sources when reading bytes without a component
file index; this path previously returned no missing-source diagnostics.

SDK readers continue returning inspection documents. No source lookup, geometry,
decoding, or resolution policy changes. The existing CLI conversion guard refuses
explicit `source_resolved: false` evidence at the root and in nested documents.
Use `kit decode` to inspect missing components and the retained cached data.

Actual subprocess coverage copies a native assembly without companion files,
checks root/child evidence in the decode report, and verifies conversion refusal
with source and destination preservation. Existing root/nested JSON cases cover
the same explicit false attribute independently of native decoding.
The native fixture uses partial decoding for inspection and can encounter an
earlier strict-read or opaque-record refusal during conversion. It does not
claim that the false-attribute guard is the sole native refusal reason.

No local tests, decoding, or test collection were executed. Pinned formatting,
type analysis and repository steering/path checks cover the change. Remote CI
must execute the process cases; no native acceptance result is claimed.
See [the missing-source gotcha](../../Gotchas/Conversion/SolidworksAssemblyResolution.md).
