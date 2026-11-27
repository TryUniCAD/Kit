# the object hook marks cited bytes directly without reconstructing the reported gaps
def MarkCitedMut(
    Coverage: dict[str, bytearray], Fields: dict[str, object]
) -> dict[str, object]:
    if Fields.get("$type") != "ProvenanceSpan":
        return Fields
    StreamName, StartPos, SpanSize = (
        Fields.get("stream"),
        Fields.get("offset"),
        Fields.get("length"),
    )
    if (
        isinstance(StreamName, str)
        and StreamName in Coverage
        and type(StartPos) is int
        and type(SpanSize) is int
    ):
        EndPos = StartPos + SpanSize
        if 0 <= StartPos < EndPos <= len(Coverage[StreamName]):
            Coverage[StreamName][StartPos:EndPos] = b"\x01" * SpanSize
    return Fields
