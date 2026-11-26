# Audit source-free Top annotation emission

The research command checks the single `*Top` schema-1 annotation serializer in a fresh Python process.
It generates the prior archive context from explicit neutral inputs and guards emission against external access.
It checks complete allocator maps, following-record readback and refusals without mutation.

## Use

```powershell
python re/solidworks/WriterResearch/VerifyAnnotationBoundary.py --root C:/trusted/KitCheckout
```

The selected checkout must contain the bounded Top serializer and its research dependencies.
The command writes a JSON report to stdout.
See the [procedure and recorded evidence](../../../../re/solidworks/WriterResearch/AnnotationBoundary.md).

## Evidence and limits

Two Python 3.14.6 process executions returned zero with identical reports.
Two generated allocator placements emitted 282 annotation bytes and 164 following bytes.
All 22 unsupported calls preserved bytes and maps.
Three additional child processes rejected unsupported or missing JSON fields before importing the serializer.
Five actual access attempts calibrated the audit guard before emission; emission triggered none.

The [allocator gotcha](../../../Gotchas/Research/Writers/AnnotationAllocationMustPreflightFutureSlots.md) records the failure found by the independent probe and the subsequent repair.
The API does not accept native annotation graphs.
Unexpected alias arguments refuse, but semantic admission of alias-bearing graphs remains unimplemented.
This command supplies no CAD acceptance, held-out proof or production promotion.
Both native acceptance flags remain false.
