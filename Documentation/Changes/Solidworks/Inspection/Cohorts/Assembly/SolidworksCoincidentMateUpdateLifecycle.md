# Trace coincident mate registration and updates

The SOLIDWORKS 2026 field record tracks the registration FILETIME, pending
update flag, solve status, and last-update version words to their native
operations. It records the conditions under which each field changes and the
order in which the modern archive stores the two FILETIME words.

The pinned image and dispatch fingerprints and the disclosed A17 archive
support this scope. The generated mate trial independently observes the cold
fields becoming saved native state. The exact runtime traversal still needs
direct measurement.

[Field rules and fingerprints](../../../../../../re/solidworks/records/CoincidentMateLifecycle2026.md)
· [Native trial](SolidworksCoincidentMateNativeProof.md)
