# Label layers use a signed sentinel

An archive condition flag alone is insufficient to locate the label layer
object. Condition bit `0x40000000` and signed selector `f48` control
the same decision. The exact value `-1` omits the field even when the
bit is set. A zero selector requests the field when the bit is set.

Read `f48` as an i16 and evaluate both predicates before reading a tag.
The supported ordinary label profile refuses an active `f50` layer.
[Exact condition and offset evidence](../../../../../../re/solidworks/records/ConfigLabelSlice2026.md)
