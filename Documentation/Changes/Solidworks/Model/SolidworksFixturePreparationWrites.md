# Preserve negative-fixture writes during optimization

The curve field-inventory process fixture now writes its 64-byte truncated
native input in a normal statement and checks the returned length separately.
Previously the write occurred inside an assertion, which optimized Python could
remove entirely, leaving an empty input instead of the intended truncated file.
The same correction applies to stdout, stderr and scope-receipt writes in the
shared curve process receipt helper.

The [review finding](https://github.com/TryUniCAD/Kit/pull/121#discussion_r4581915614)
was verified directly against the changed source. Input selection, exclusive
file creation, expected hash, strict CLI flags, timeout and all result assertions
remain unchanged. The repair adds no new command or production behavior.
Receipt contents and length checks are unchanged; their writes now run independently
of assertion optimization.

Verification is static source/AST and formatting review only. No local tests,
optimized reproduction, schema or codec execution occurred. Fresh current-head
remote checks remain pending. See the
[fixture-write gotcha](../../../Gotchas/Ci/ProcessChecks/FixtureWritesMustNotBeAssertions.md)
and [field-inventory process contract](SolidworksCurveFieldInventory.md).
