# Source inspection can read during construction

## Expectation

Adding diagnostic metadata about a callable does not read a file or change a fresh
writer's dependencies.

## Actual behavior

`inspect.getsource` can open the callable's Python source file through the source cache.
The shared research round-trip checker also runs inside the fresh-construction process's
existing read-denial boundary.
Its new raw-operation reporting therefore attempted eight reads of `ResolvedDims.py`
while checking each constructed part.

The [remote process job](https://github.com/TryUniCAD/Kit/actions/runs/43784683947/job/133029564572)
on `6047d1d5594210cdfbe13b2c3aea45e5105b866f` reported two failures, 165 passes and
158 fixture-dependent skips.
Both failures were the existing assertion that `denied_reads` is empty.
The source archive round-trip checks passed in that run.

## Workaround

Record callable identity, source filename and first source line from the in-memory
code object. Do not retrieve the source text during load, store or construction.
Keep the text field null with an explicit status and inspect the independently
authored schema outside the execution boundary.

The repair removes source retrieval and keeps the original read-denial checks.
It changes no serialized field, schema plan or writer output rule.
Remote verification of the repaired revision remains pending.

See the [schema-usage contract](../../../../Changes/Solidworks/Model/SolidworksArchiveSchemaUsage.md)
and [fresh process boundary](../../../../../tests/convert/solidworks/research/FreshPartProcess.py).
