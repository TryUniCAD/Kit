# Observe initial document update

The native observer accepts `--profile frame` for the initial document update boundary.
It records entry into the selected template method and its runtime virtual target.
It also records native exception details through Frida's process exception callback and forwards each exception unchanged.

The 2026 application exception metadata places the critical repair handler around the initial-update virtual call.
The [critical repair record](../../../re/solidworks/records/CriticalRepair2026.md) identifies the binary and error mapping.
This profile omits archive, sketch and model-finalization hooks.
Native exception handling remains an observation whose neutrality must be checked against healthy controls.

The report retains exception type, instruction location, memory operation, register values and available native backtrace entries.
Backtrace entries are provider output and do not establish a validated call chain.
The callback does not expose every original Windows exception parameter.
Static syntax inspection passed. Controlled measurements remain pending.
