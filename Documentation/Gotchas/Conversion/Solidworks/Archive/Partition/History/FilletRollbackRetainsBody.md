# Edge fillet rollback retains the body slot

The selected mark in four SOLIDWORKS 2026 SP05.2 single-edge fillet saves begins with populated restored records. The first restores the prior stock's implicit body name. A separate previous-copy record restores the BODY in its existing slot. The body keeps the same atom and matching tag while its last modifier returns to the stock feature. [Measured rollback](../../../../../../../re/solidworks/records/EdgeFilletRollback2026.md)

The ordinary delete-only reader expects an empty restored list, one previous WORLD and removal of the selected body. For a fillet, decode the full typed delta and verify the previous graph before asserting body lineage. The succeeding stock rollback owns the deletion.
