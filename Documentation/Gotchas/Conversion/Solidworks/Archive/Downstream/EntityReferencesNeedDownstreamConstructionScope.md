# Entity references use an active downstream construction scope

## Expectation

Calling a fresh native face/edge reference constructor creates the same embedded downstream data regardless of its caller context.

## Actual behavior

The exact 2026 model create path temporarily publishes the actual downstream data object to global `0x4db5dd20`. BEnt semantic initialization allocates `moEntRefDownstreamIdData_c` at `f18` only while that scope is active. Indexed face insertion then resolves actual faces through the active object's allocated face rows. This is separate from the archive helper's serialization flag.

A default object with null `f18`, or an independently created empty map with invented IDs, does not implement this model relationship. Face-before-edge creation also supplies the face identity map used by edge validation.

## Workaround

Represent the scope as explicit generated graph ownership: actual downstream object, actual BEnt parent backlink, actual component and indexed face-role associations. Conversion must not invoke the native constructors, copy native globals, or require a CAD runtime.

[Exact source record and hashes](../../../../../../re/solidworks/records/DownstreamFreshReferenceAssignments2026.md) bind enter `0x4b51de40`, leave `0x4b51f880`, initialization `0x4b74bfc0` and the indexed map setter `0x4b53b540`. Usable generated references still require independent native qualification.
