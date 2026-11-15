# Independent deletion does not prove a minimum stream set

## Expectation

If each stream opens when removed separately, all such streams can be omitted together.

## Observed behavior

The [2026 deletion study](../../../../re/solidworks/v2026/Deletion2026.md)
removed one stream at a time from one boss part.
It did not measure removal of the complete optional set.
Independent deletions can retain a fallback or a dependency in another stream.
The seven individually critical streams are therefore not a proven minimum container.

## Workaround

Measure a combined omission with healthy controls before using that stream set.
Include model-bearing streams when the source has their information.
Keep separate deletion evidence and generated-writer acceptance evidence.
