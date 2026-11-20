from struct import pack as PackValues


# the independent wire fixture declares its own native class tags
def MakeMgrDesc(ClassName: str, SchemaValue: int = 1) -> bytes:
    NameBytes = ClassName.encode("ascii")
    return PackValues("<HHH", 0xFFFF, SchemaValue, len(NameBytes)) + NameBytes
