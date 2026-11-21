# JSON readers validate documents even when strict mode is disabled

## Expectation

A caller might expect `open_document(path, strict=False)` to reopen a deliberately malformed neutral graph for inspection.

## Actual behavior

The JSON adapter validates the complete model before filtering. Ordinary reads use `CadDocument.from_json`. An explicit configuration read decodes the typed model, selects the requested configuration, and validates the complete graph with that configuration active. `ReadOptions.strict` controls the second validation after filtering. A missing entity or parameter reference still raises `DocumentError` before a writer receives the graph.

The [remote native-field cases](https://github.com/TryUniCAD/Kit/actions/runs/43668887044/job/132674284143) exposed this expectation at `ef431a17`. The source path is `JsonReader.ReadAction` → `DocumentIo.FromJson` → `AssertValid`.

## Workaround

Keep the public reader's structural rejection. For explicit inspection of deliberately unresolved graphs, use the low-level `interchange.serialization.JsonCodec.LoadJson` decoder, check the returned model type, and retain its original evidence. This does not qualify the graph for writing. Regression cases separately require conversion to reject malformed persisted input and direct/public writes with validation disabled to reject unresolved required semantics before output mutation.

See [native field refusal](../../Changes/Research/Readers/NativeFieldWriteRefusal.md).
