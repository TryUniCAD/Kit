# Imported counts follow the bound solid

An imported feature can have one complete decoded local B-rep and
zero design solids in the summary derived from parametric operations.
The ordinary decoder can select the local wrapper before the manual
local geometry fallback runs.

Compute the counts after binding the actual local import, its
feature-to-atom reference and the selected payload to the design body.
Keep the existing geometry and bounds. A closed body alone supplies
insufficient evidence to change the local design count.

[Originals, native saves and removal comparison](../../../../../../../re/solidworks/measurements/2026/ImportedNativeKeywordTopology01.json)
