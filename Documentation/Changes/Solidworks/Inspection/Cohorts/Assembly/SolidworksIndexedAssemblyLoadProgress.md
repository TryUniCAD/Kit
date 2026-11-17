# Recognize indexed assembly-loading progress

The SOLIDWORKS assembly observer admits the native `Opening Component N of M` progress label when the counters are positive and ordered. The existing owner, title, stage, button and detail checks still apply. The observer records progress without dismissing the window.

Run `ReplayIndexedAssemblyProgress.py <first-disclosed-results-directory>` to reproduce the classifications in a separate host process. The replay recognized both captured indexed observations and three established progress labels. It rejected eleven malformed or modal variants. These classifications preserve the first native batch's failed status.

For native confirmation, run `ReplayNestedAssemblyReopen.py prepare <first-results-directory> <pinned-native-control> <unused-sibling-deck>` on the host. Run its frozen `run` command with the replay manifest and digest in the pinned oracle. The tool reopens the two original disclosed assemblies read-only at their original paths. It checks all source file hashes and brackets the two reopens with fresh control processes. It writes only to the new replay directory. Native confirmation remains pending at this change's host verification stage.

[Process reproduction](../../../../../../re/solidworks/measurements/2026/AssemblyIndexedProgressReplay01.json) · [Indexed progress gotcha](../../../../../Gotchas/Conversion/Solidworks/Oracle/Assembly/IndexedComponentLoadProgress.md) · [Same-path replay tool](../../../../../../re/tooling/sw2026/ReplayNestedAssemblyReopen.py)
