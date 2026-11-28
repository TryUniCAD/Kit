# Standalone self locators are not child references

A native self-file record looks like an external-file reference, but its path is
not automatically a load dependency for a standalone generated part. The measured
Unicode-named SDK part opens, edits, saves and reopens cleanly from a different
UNC location while its archived C: self locator is absent before and after.

The narrow host-preparation policy may therefore retain the explicitly authored
`C:\KitSdkCandidates` self namespace while preserving the exact neutral basename.
The actual host output location stays separate. This is not a filesystem mapping,
a reason to omit the self record, or permission to ignore an assembly occurrence
or drawing child path.

Keep linked/multi-file modes outside this policy, use their actual qualified child
references, and fail unsupported modes explicitly. Do not broaden the placeholder
namespace from this one standalone observation. The public writer remains disabled.

The [relocation receipt](../../../../../../re/solidworks/measurements/2026/SdkPartRelocation01.json)
and [source rule](../../../../../../re/solidworks/records/SdkStandaloneHostPath2026.md)
record the exact distinction and remaining acceptance scope.
