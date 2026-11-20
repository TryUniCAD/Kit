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
