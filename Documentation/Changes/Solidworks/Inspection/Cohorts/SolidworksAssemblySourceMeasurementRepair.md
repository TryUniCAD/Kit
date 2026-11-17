# Measure assembly source geometry with an observation-only load monitor

The first source attempt is ineligible. The native assembly loader showed a
different progress window from the existing part/drawing path. The generic
watchdog clicked Close even though the empty assembly had opened with zero
errors or warnings. Separately, a resolved copy of the control part reported
the correct volume and area but a different absolute mass in assembly context.

The [assembly monitor](../../../../../re/tooling/sw2026/ObserveAssemblyLoad.py)
records the exact owned loading stages without a window action. The source
author verifies each placement and body, then measures volume, area and centre
of mass. It retains absolute mass without assuming the isolated part's density
default also applies in the assembly. Material equivalence is outside this
source batch.

The [first attempt receipt](../../../../../re/solidworks/measurements/2026/AssemblySourceAttempt01.json)
records all six source phases, healthy controls and unchanged licensing.
The [replacement cohort](../../../../../re/tooling/sw2026/AssemblySourceSpecs02.json)
uses new native source names and distinct held-out placements. The original
results stay failed. The revised cohort remains unmeasured at this revision.
