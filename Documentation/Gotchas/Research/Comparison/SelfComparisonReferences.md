# Self comparison with unresolved references

## Expectation

Comparing a decoded document with itself can appear to guarantee equality or only an unresolved status.

## Actual behavior

The historical `solidworks-058` neutral control export contains a selection target named `Sketch1`, while the projected sketch identity is `sldprt:sketch:26`.
The graph retains that dangling target as an unresolved reference.
Reference comparison can consequently record differences even when both input documents contain the same unresolved target.
Self comparison therefore does not guarantee a particular primary outcome or semantic qualification.

## Workaround

Inspect detailed source issues and dependency differences alongside the primary status.
Preserve the original source evidence and report unresolved batches with exit `3`.
Do not rewrite source identities or suppress unresolved references merely to obtain equality.

The committed-export process case in `tests/Research/Archives/Comparison/BulkExportTests.py` allows these honest outcomes while requiring matched features, retained source issues and unchanged source hashes.
Its process execution remains assigned to the remote shared suite; no decoder or CAD application ran locally.
