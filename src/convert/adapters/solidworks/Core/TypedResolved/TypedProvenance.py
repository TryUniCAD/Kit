from collections.abc import Mapping

from convert.adapters.solidworks.Container.Format import KInfoValue
from interchange import Provenance, ProvenanceSpan


# typed record provenance must not pretend that an object offset identifies its scalar field
def TypedProvenance(
    OwnerValue: Mapping[str, object], NativeId: str
) -> Provenance | None:
    StreamName = OwnerValue.get("stream")
    OffsetValue, EndValue = OwnerValue.get("offset"), OwnerValue.get("end")
    if (
        type(StreamName) is not str
        or type(OffsetValue) is not int
        or type(EndValue) is not int
        or EndValue <= OffsetValue
    ):
        return None
    return Provenance(
        adapter=KInfoValue.format_id,
        native_id=NativeId,
        spans=(
            ProvenanceSpan(
                StreamName, OffsetValue, EndValue - OffsetValue, "typed-archive-object"
            ),
        ),
        confidence=1.0,
    )
