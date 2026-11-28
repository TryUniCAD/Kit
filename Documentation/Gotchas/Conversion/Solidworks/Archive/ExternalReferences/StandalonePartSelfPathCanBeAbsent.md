# A standalone part self path can be absent

A generated standalone blind-boss part has an absolute Windows self path
in its headers. SOLIDWORKS 2026 opened the same-named file directly from a
UNC location even though the archived path stayed absent. Opening used
the caller's exact file path. An edit, new save and fresh reopen preserved
the feature tree, depth and geometry.

For the measured standalone profile, a Windows self locator can satisfy
the wire field while the caller supplies the actual destination. Keep the
authored basename consistent. Linked part references still need their
own native identity checks. [Relocation measurement](../../../../../../re/solidworks/measurements/2026/SdkPartRelocation01.json)
