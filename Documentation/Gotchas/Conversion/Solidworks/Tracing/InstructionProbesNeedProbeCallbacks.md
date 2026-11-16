# Interior instruction probes use a probe callback

## Expectation

A function-entry callback object can also serve as an arbitrary interior-instruction probe.

## Actual behavior

[Frida documents](https://frida.re/docs/javascript-api/#interceptor) a separate function form for arbitrary instructions. Function-entry argument interpretation can be invalid after registers and stack have changed. Entry/return callback semantics should not be borrowed for a mid-function site.

## Workaround

Use a single probe function at each interior site and read only its verified register context. Keep entry/leave callback objects at actual function entries. The [training contract](../../../../../re/solidworks/records/RadialTrainingObservation2026.md) uses six probes and five function listeners, with complete owning-function identities and mapped instruction checks. This is static API/source review; runtime relocation and capture remain pending.
