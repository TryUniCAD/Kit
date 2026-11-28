# SOLIDWORKS concentric assembly parent light oracle

The [measurement tool](../../../../../re/tooling/sw2026/para/concentric/MeasureConcentricParentLights.py)
prepares a disclosed concentric assembly pair with one distinct parent light
name, colour and coefficient set. It uses the same independent mate and
geometry predictions and the same disclosed controls as the aligned trial.
The ordered native feature tree is measured before and after rebuilding and
saving, then again after opening the native save in a fresh process. The
typed readback checks the authored scene fields in both packages.

This tool uses the exact SOLIDWORKS 2026 SP05.2 observer closure for disclosed
geometry and light evidence. Public admission and held-out acceptance are
outside this comparison.

All four native processes passed. The generated pair kept its authored light
through cold open, rebuild, a linked child depth edit, save and fresh reopen.
It passed 84 numeric checks, including geometry and driving dimensions.
The typed native save matched all 60 light fields.
[Native lifecycle receipt](../../../../../re/solidworks/measurements/2026/ConcentricParentLightsNative01.json)
