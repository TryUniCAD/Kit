# Collected surface copies start unindexed

The SOLIDWORKS 2026 downstream surface clone copies its keeper and allocates a distinct typed file object when the original has one. The copied file resets its list index to `-1` and its save-time field to zero. The referenced configuration is assigned separately and the shared file definition retains its identity.

Give each copied file object its own archive slot and preserve its shared string handles. Keep the list index and configuration ID independent. [Source and replay](../../../../../../re/solidworks/records/DownstreamCollectedSurfaceClones2026.md)
