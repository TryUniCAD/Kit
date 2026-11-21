# The saved solid count is owned by the configuration

An ordinary SOLIDWORKS configuration stores a signed solid-body count separately from its kernel partition. A generated prism can have one body in its active partition while retaining the fresh configuration count of zero. A native save of the same geometry records one.

For the ordinary complete save profile, derive the stored count from the actual atom manager's solid-body inventory. Keep a separate measurement of the number returned during load and the final model body inventory. The ordinary loader can request an update and clear bodies when its expected count is greater than the returned sum. [Pinned source and disclosed counts](../../../../../../re/solidworks/records/PrismOpenBodyAdmission2026.md#persisted-body-bookkeeping)
