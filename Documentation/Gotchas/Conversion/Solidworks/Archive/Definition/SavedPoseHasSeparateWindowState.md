# Saved document pose has separate window state

An ordinary part can store a document view pair and a saved user
environment in the same Definition. The L1 and OneLights controls
each contain both.

Use `fae8` and `faf0` to inspect the saved document orientation and
pan/zoom. Follow the saved window and its independent transform owners
when a task requires the active session view.
[Native caller and process evidence](../../../../../../re/solidworks/records/SavedPartViewRead2026.md)
