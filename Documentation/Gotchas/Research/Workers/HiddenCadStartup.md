# Hidden CAD startup

Setting SOLIDWORKS visibility after COM binding does not prevent startup windows from appearing. Fusion's desktop API also runs in a licensed desktop application.

The personal worker now requests hidden process startup and hides visible windows only for the exact launched process ID. It does not enumerate window titles, dismiss dialogs or hide unrelated interactive sessions. Private source backups remain on the PC. This is desktop window suppression, not a headless production CAD dependency, and it cannot prove that no window ever briefly appears.

Both applications authored three independent canary files with matching requested/native volumes. A final owned-window check found zero visible windows in each session. Full native work resumed afterward. Per-batch binding to the external helper revision was not independently attested; preserve that limit with the [hidden-window evidence](../../../../re/NativePlacement2026/HiddenWindowEvidence.json).

The same campaign later retained a SOLIDWORKS COM/RPC failure and supported recovery. Hidden operation does not establish that the crash is fixed or authorize silently treating native failures as successful.
