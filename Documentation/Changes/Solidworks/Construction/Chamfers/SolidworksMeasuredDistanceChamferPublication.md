# Publish measured distance chamfer parts

Kit can publish equal-distance and two-distance SOLIDWORKS 2026 SP05.2
chamfers after validating the exact offline native measurement. The neutral
document contains one blind rectangular Front stock, its selected edge and
first incident face, and the actual D1 or D1 and D3 driving parameters.

Pass a `solidworks_native_measurement` envelope in `write_document` or
`WriteOptions.values`. The envelope carries the authorized construction
epoch and the matching generation and native result reports. For the two
pre-writer locked cases, use the parsed protected report as
`receipt.native_report`. An empty, seekable binary stream also needs the
exact measured `final_destination`. A file write must reproduce the
measured encoded locator.

Kit compares the full regenerated archive to the measured input hash
before publication. The disclosed files reproduce through registry and
direct SDK streams. Failed or mismatched measurements preserve the final
destination. Both retained native edit and fresh reopen phases and their
healthy controls are part of the receipt. [Usage and proof](../../../../../re/solidworks/records/ChamferDistancePairPublication2026.md)

The original Windows view arithmetic reproduces both locked artifacts.
The registry, adapter and direct writer match all ten logical streams
per part. Twenty-four refusal checks preserve caller-owned sinks.
[Held-out publication proof](../../../../../re/solidworks/measurements/2026/SdkHeldoutDistanceChamferPublication01.json)
