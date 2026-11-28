# Correlate assembly directory timestamps with their child records

The synchronized source readback includes `Contents/CMgrHdr2` for all
five disclosed files. It retains configuration data and the manager's
save timestamp, the file headers' self timestamps, and the file
directory's persisted state alongside the occurrence update checks.

The readback checks 40 archive round trips and records eight direct
timestamp comparisons for the one-child and repeated-child assemblies.
The [remote receipt](../../../../../../re/solidworks/measurements/2026/AssemblyChildFileTimes8060.json)
records 40 exact comparisons and eight timestamp matches. The
[native timestamp trace](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#child-directory-timestamp-sources)
identifies the two directory sources and the clock fallback.
