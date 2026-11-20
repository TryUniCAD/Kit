from struct import pack as PackValues


# independent child bytes keep the model id in its documented signed word
def MakeCfgBody(IdValue: int) -> bytes:
    return (
        PackValues("<i", 1)
        + b"\xff\xfe\xff\x02P\x00\xbb\x03"
        + PackValues("<iI", IdValue, 4_000_000_012)
        + b"\xff\xfe\xff\x05"
        + "Stock".encode("utf-16-le")
        + PackValues("<ii", -1, 1)
        + b"\xff\xfe\xff\x04"
        + "Note".encode("utf-16-le")
        + b"\xff\xfe\xff\x00"
        + PackValues("<iiII", -3, 7, 3_000_000_000, 101)
    )
