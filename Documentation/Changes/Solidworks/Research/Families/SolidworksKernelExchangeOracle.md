# Calibrate binary Parasolid exchange in SOLIDWORKS

The [exchange observer](../../../../../re/tooling/sw2026/imported_body_source/ObserveKernelExchange.py)
uses the ordinary binary Parasolid translator of SOLIDWORKS 2026 SP05.2.
It first exports a native box in its fresh process, then imports that file
and independently measures the cold and rebuilt solid. It records the
original 3D Interconnect preference and restores it after each phase.

Both application and native-export controls bracket the candidate lanes.
The source-built and generated bare-body samples have distinct roles.
The first exchange observation is pending. Native archive acceptance
requires separate measurement of generated part containers.
