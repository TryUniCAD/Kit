# Edge repair can replace earlier rows

**Expectation:** post-insert edge validation only decides whether to keep the current row, and a rebuilt reference needs a new downstream ID.

**Actual behavior:** a key collision can first reconstruct the earlier matching row with mode 0, replace its component pointer and mark its row ordinal. The outer caller can independently replace the current row after a false validation result. Both pointer replacements preserve the already allocated row ID. A separate Boolean and out-status control current-reference acceptance.

**Workaround:** keep row ordinal, allocated ID, actual edge, body atom and reference pointer as separate typed owners. For the bounded fresh prism, require absence of both original and applicable anti keys before taking the unchanged-reference branch. Never renumber a row merely because its pointer changed, and never clear incoming `fe8` on the collision-free path without a separate source rule.

The [source record](../../../../../../../re/solidworks/records/DownstreamEdgeValidation2026.md) supplies exact original ranges and limits. General collision and later teardown/store behavior remain unqualified.
