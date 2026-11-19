# Observe raw Parasolid bodies in SOLIDWORKS

The [kernel probe](../../../../../re/tooling/sw2026/imported_body_source/ObserveKernelBodyRestore.py)
measures the versioned COM path from a raw Parasolid stream to a temporary
body and a native BaseBody feature. Native body Save-to-Restore controls
and a pristine part open bracket the run. The packet declares the file
hash, topology, vertex coordinates and mass properties of each supplied
body. The observer uses a fresh exact-build process for each lane.

The [first binding receipt](../../../../../re/solidworks/measurements/2026/LocalKernelDynamicRestore01.json)
records two successful pristine application controls and two failed native
stream controls. Both same-method native streams reach
`IModeler::Restore`, which returns `0x80004002` before a body is returned.
The packet opens no candidate. The generated IUnknown binding has a separate
control lane. Native writer and archive acceptance require their own cold
open, save and fresh-reopen procedures.
