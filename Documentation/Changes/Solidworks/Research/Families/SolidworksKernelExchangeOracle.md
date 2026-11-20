# Calibrate binary Parasolid exchange in SOLIDWORKS

The [exchange observer](../../../../../re/tooling/sw2026/imported_body_source/ObserveKernelExchange.py)
uses the ordinary binary Parasolid translator of SOLIDWORKS 2026 SP05.2.
It first exports a native box in its fresh process, then imports that file
and independently measures the cold and rebuilt solid. It records the
original 3D Interconnect preference and restores it after each phase.

Both application and native-export controls bracket the candidate lanes.
The source-built and generated bare-body samples have distinct roles.
The [native receipt](../../../../../re/solidworks/measurements/2026/GeneratedLocalKernelExchangeNative01.json)
records seven healthy processes. The native archive's local body and
two generated bodies import successfully. Both generated bodies retain
their topology, volume, area and centre of mass before and after rebuild
through 140 candidate comparisons. Native archive acceptance requires
separate measurement of generated part containers.
[Preference readback gotcha](../../../../Gotchas/Conversion/Solidworks/Oracle/Parts/ExchangePreferenceNeedsReadback.md)
