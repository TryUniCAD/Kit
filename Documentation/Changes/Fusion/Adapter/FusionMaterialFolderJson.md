# Fusion material resource folders in public JSON

The strict Fusion reader retains typed material resource folders in the document's version-2 public JSON. Folder metadata, child order, linked resource metadata and file contents survive persistence with the rest of the model.

Use the existing public SDK reader and JSON APIs.

```python
from convert import open_document
from interchange import CadDocument

document = open_document("Source.f3d")
reloaded = CadDocument.from_json(document.to_json())
```

The affected saved files retain `fusion.read_only`. The existing bounds still apply, including eight levels for material folder traversal and 2,000,000 bytes for an individual value in public JSON state. Material resource authoring, procedural material compatibility and Fusion application verification are separate requirements. See the [material resource JSON gotcha](../../../Gotchas/Conversion/Fusion/Materials/FusionMaterialResourceState.md).

## Verification

The strict SDK previously refused the retained resource-bearing archive with `Unsupported Fusion semantic-state value`. After registration, the same archive with SHA-256 `53e4d1325cf45180a88d1c701cdbac88a6744af0d27d08481c781c5749c15739` opened and reproduced its complete lower document model after public JSON reload. It retained the version-2 read-only contract.

An independent typed-state case verified empty resource content and all 256 byte values. Six unchanged refusal checks covered unknown classes, missing fields, malformed base64, unsafe folder names, resource count mismatch and mixed child/resource folders.

All six affected SDK and package compatibility cases passed in 8.54 seconds. They also verified that writer refusal preserves an existing destination when the descriptive read-only flag is present or removed from the JSON.
