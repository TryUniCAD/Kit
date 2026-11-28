# Configuration construction clears its node update state

## Expectation

A fresh configuration retains the ordinary feature constructor's dirty flag
`f0c=1`.

## Observed behavior

The active 2026 base-configuration constructor names the node, then explicitly
calls the node update setter with status zero. The setter applies mask
`0xfffd7ff8`, clearing that initial flag. The part-derived constructor and the
first manager selection do not re-mark the configuration node.

The embedded part-configuration object has a separate `f0c` field. Its native
constructor leaves that field at one; it is not the feature node's update flag.

The [construction record](../../../../../re/solidworks/records/ModelConstruction2026.md#configuration-construction)
identifies the constructor call, setter, concrete part constructor and initial
manager-selection rules in the exact target binary.

## Workaround

Apply the proven zero-status transition to the actual configuration feature
node during base construction. Preserve the embedded object's independent
constructor state. Derive subsequent dirty transitions from the operations that
cause them, rather than carrying an inherited seed forward.
