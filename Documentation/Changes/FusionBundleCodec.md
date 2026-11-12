# Fusion bundle envelope codec

## Behavior

`BundleCodec` reads and writes the qualified Fusion `.f3z` envelope profile.
Immutable models expose document identities, graph roots, typed reference groups, role metadata, and document members.
The codec handles one closed design graph with description version `0.1`.

`ReadBundle` validates ZIP framing, bounded JSON, exact member ownership, unique identities, and graph references.
It rejects cycles, unreachable documents, duplicate JSON keys, unsafe member names, unknown fields, and unsupported packaging variants.

`EmitBundle` derives JSON and ZIP framing from typed values.
Callers supply each complete serialized F3D or F2D document through `BundleFile`.
Document payloads remain byte-exact. Outer compression and JSON whitespace can change.
The bundle layer does not claim to decode or convert a member's parametric or drawing content.

## Usage

Import the public functions from their defining modules:

```python
from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle

Bundle = ReadBundle(SourceBytes)
OutputBytes = EmitBundle(Bundle)
```

`SourceBytes` must contain the complete supported F3Z archive.
The example illustrates the API and was not executed locally.
Callers can also construct `FusionBundle` from typed descriptions and independently authored document bytes.

The reader accepts an optional `InflateZstd` callback for compatible compressed members.
The emitter uses the existing deterministic ZIP writer and requires no CAD runtime.

## Limits

The maximum archive size is 128 MiB, with at most 4094 documents.
Each document is limited to 64 MiB. Each JSON envelope is limited to 4 MiB.
JSON depth is limited to 32, with at most 100,000 nodes and 1 MiB per string.

The qualified profile rejects multiple graphs, external `designObjectRefs`, sharing descriptors, and secondary object packaging.
Application-specific metadata remains typed text. The codec preserves embedded JSON strings without interpreting their application semantics.
Nested document validation remains the relevant document codec's responsibility.

F3D XREF bundles have supplied corpus evidence.
F2D and DERIVED envelope tags follow the upstream specification but lack supplied native acceptance evidence.

## Verification

Raw research inspection found nine F3D documents and eight XREF links in the supplied bundle.
All seventeen repeated document identities match their description records.
All eight role links match the root document's `RedirectionsStream.dat`.

Integration coverage crosses the existing ZIP reader, typed bundle codec, nested redirection stream, and ZIP writer boundaries.
It covers complete document preservation and rejects missing targets and unindexed members.
Tests were not executed locally. Remote CI and native upload acceptance remain separate requirements.
Black, steering compliance, Mypy, Ruff, and Pyright passed for all 32 new production and integration Python files.
Pyright reported three existing unrecognized configuration settings and no code errors or warnings.

See the [detailed bundle data model](../../re/Fusion/Reconstruction/BundleAuthoring/BundleDataModel.md)
and [inspection evidence](../../re/Fusion/Reconstruction/BundleAuthoring/BundleEvidence.json).

## Native import

The public archive import API accepts F3D only.
F3Z acceptance requires an asynchronous upload through `DataFolder.uploadFile`.
See [the F3Z import boundary](../Gotchas/Conversion/FusionBundleUpload.md).
