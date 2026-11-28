# Verify native edits for FreeCAD 1.0 and 1.1 origin boxes

The internal origin-box recipe builds two disclosed neutral sources
from FreeCAD 1.0.2 and 1.1.4. On SOLIDWORKS 2026 SP05.2 both parts open
without warnings, rebuild with their named solid and accept independent
Length, Width and Height edits. A clean save and fresh reopen preserve
the final Height, original Length and Width, custom kilogram setting
and all 19 or 22 source text properties.

`InspectFreecadBoxReleasesNative.py` runs the frozen native packet with
two independent known-good controls. `QualifyFreecadBoxReleasesNative.py`
reads the checksum-bound generated and native-saved containers in the
SDK. All four strict reads and forty typed or keyword stream comparisons
pass. The native scopes cover ordinary independent AdditiveBox profiles.
Native material and appearance assignments, public export admission and
historical-corpus membership require separate evidence.
[Protocol and results](../../../../../re/solidworks/records/FreecadOriginBoxReleases2026.md)
[Measurement](../../../../../re/solidworks/measurements/2026/SdkFreecadBoxReleaseNative01.json)
