# A stock depth can lack an exact millimetre inverse

The cold pattern stock drivers store binary64 lengths in metres.
Returning the displayed millimetres to a millimetre-only writer can move
the metre word even when the visible depth agrees. The disclosed
`ColdRaisedPatternA` plate D1 is stored as (0.0065\) metres and the
millimetre multiplication path cannot regenerate that exact input.

Keep the physically linked metre parameter and derive the public display
from it. A cold readback reconstruction can supply that same quantity in
metres to the generative planner, after checking it still agrees with the
public parameter and extrusion definition. The existing whole readback
and native digest checks protect the final output.

[Measured pattern reproduction](../../../../../../re/solidworks/records/MeasuredLocalLinearPattern2026.md)
