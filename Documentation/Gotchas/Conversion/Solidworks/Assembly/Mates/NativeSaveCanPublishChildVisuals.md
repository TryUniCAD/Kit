# Native save can publish the child's visual store

The generated radial assembly retains its named visibility states at
initial cold open with no VisualStates stream in the generated child.
Saving the changed driving depth creates a 1,817-byte child visual
store. Both named mixed states still apply to the same occurrence IDs
after the paired save and fresh native reopen.

Check the exact generated child bytes before first open when measuring
whether the parent can use that child without its own visual store.
Bind the native saved child separately.

[Same-locator native comparison](../../../../../../re/solidworks/measurements/2026/ConcentricRadialDisplayNative01.json)
