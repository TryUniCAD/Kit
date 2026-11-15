# Source archives can survive outside payload records

The SOLIDWORKS reader's source-retention path stores original archive bytes under document metadata key `solidworks_source_bytes`.
Neutral JSON can preserve those bytes even when the feature timeline and B-rep are typed.
Checking only `BrepPayload` records therefore does not establish that retained native bytes are absent.

The CLI refuses that retained-source key regardless of its value, and refuses binary metadata values under aliases or nested containers.
The check applies independently to embedded assembly documents.
Use `kit decode` for inspection; replacing the source archive with a digest or text provenance does not create new conversion qualification.

JSON process fixtures cover `bytes` and its supported map/list/tuple/set/frozen-set containers.
The wire serializer does not support `bytearray`, `memoryview`, or cyclic containers, so those broader scan branches cannot be reached through an ordinary JSON source fixture.
See [the change entry](../../../Changes/Commands/RetainedMetadataGuard.md).
