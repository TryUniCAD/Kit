from struct import pack as PackValues, unpack as UnpackValues


# native raw transform words are computed from the identity matrix state translation scale and explicit neutral padding
def MakeRawIdentity() -> dict[str, object]:
    Matrix = tuple(
        float(RowValue == ColumnValue)
        for RowValue in range(3)
        for ColumnValue in range(3)
    )
    DataValue = PackValues("<9dII4dII", *Matrix, 1, 0, 0.0, 0.0, 0.0, 1.0, 0, 0)
    return {
        "words": tuple(
            {"w": WordValue} for WordValue in UnpackValues("<30I", DataValue)
        )
    }
