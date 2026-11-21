# Saved thin revolve cache uses two marks

A valid Parasolid delta payload can describe a different state from the thin revolve in the archive. On the disclosed SOLIDWORKS 2026 SP05.2 files, the current kernel mark agrees with the producing feature's `moPMarkRecord_c` at `f3d0`. Its predecessor agrees with the configuration model's `fe38` record. Both use the typed mark ID at `f18`.

Compare each mark with its owner after validating the active and rollback graphs. The predecessor stays 3 in these controls. The feature's current mark changes from 7 before editing to 13 or 15 after editing, so matching the predecessor alone cannot establish the active save's lineage. [Source and guarded readback evidence](../../../../../../re/solidworks/records/ThinRevolveSavedRead2026.md)
