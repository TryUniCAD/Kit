from convert.Geometry.Parasolid import KTerminalFinSchema, ParaHeader, ParaHeaderData


# strict refusal applies to the same transmit role as the sequential local decoder
def ReadLocalHead(DataValue: bytes) -> ParaHeader | None:
    HeaderValue = ParaHeaderData(DataValue)
    if (
        HeaderValue is not None
        and HeaderValue.schema == KTerminalFinSchema
        and HeaderValue.description
        == ": TRANSMIT FILE created by modeller version 3701250"
    ):
        return HeaderValue
    return None
