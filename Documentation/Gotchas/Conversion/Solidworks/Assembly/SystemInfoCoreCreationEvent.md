# The assembly information creation date has its own event

## Expectation

The binary assembly header creation timestamp can also supply `SW-Created Date`.

## Observed behavior

The twelve disclosed version-19000 files have the same creation timestamp in both binary headers. The core creation event is zero to four seconds later. In D01 it is one second later in both saves. The core modification event equals the actual self-file save event `f60` in both headers across all twelve files. [Receipt](../../../../../re/solidworks/measurements/2026/SdkAssemblyInformation01.json)

## Workaround

Use the authored core creation event for `SW-Created Date` and verify the actual paired self-file save event for the saved date. Supply the local offset explicitly to format both clock values. Preserve the binary header creation event for the document's file identity.
