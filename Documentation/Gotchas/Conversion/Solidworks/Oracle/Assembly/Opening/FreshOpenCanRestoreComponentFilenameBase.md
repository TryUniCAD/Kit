# Fresh open can restore the component filename base

An ordinary custom `IComponent2.Name2` assignment can return the intended name
through both component and feature APIs and save cleanly. The 2026 SP05.2
disclosed trial temporarily disabled `swExtRefUpdateCompNames`, wrote two
distinct base names, saved the child and assembly, and restored the original
enabled preference. On a fresh open, the same two occurrence IDs reported the
shared child file's base and their original instance suffixes through both APIs.
Controls passed.

Measure fresh-process names with the intended user preference and compare the
actual occurrence IDs, paths and feature identities. Preserve the filename and
stored base as separate observations while tracing the native open decision.
The live setter and successful save establish those two operations only.

[Native receipt](../../../../../../../re/solidworks/measurements/2026/CustomComponentBaseNameRetryNative01.json) · [Base-name setter trace](../../../../../../../re/solidworks/records/ComponentBaseNameSetter2026.md)
