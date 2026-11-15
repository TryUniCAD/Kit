# Cached assembly meshes do not establish loaded component sources

An isolated SOLIDWORKS assembly can retain component display meshes and original
source paths while none of its external component documents are available.
Previously its part definitions exposed those paths without an explicit loaded
source flag. Reads with an empty component file index also returned no
missing-source diagnostics, so path or diagnostic checks could miss the gap.

Definitions now record `attributes.source_resolved`: the decoded root is true;
other definitions are true only when their referenced document was actually
loaded. Cached meshes do not change false to true. Source paths remain provenance
and are not used to infer missing sources in constructed typed JSON documents.

Use `kit decode` to inspect these documents. The CLI conversion guard rejects
explicit false flags, including within nested documents, while SDK inspection
remains available. This evidence does not establish recovered feature semantics
or target-application acceptance.

See [the adapter](../../../src/convert/adapters/solidworks/core/Adapter.py),
[the change entry](../../Changes/Solidworks/AssemblyResolutionEvidence.md), and
[CLI process coverage](../../../tests/convert/Commands/CliAssemblyTests.py).
