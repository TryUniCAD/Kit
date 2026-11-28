from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# unsigned kernel identities use signed wire words without becoming persistent feature identifiers
def ReadDownstream(Value: object) -> int:
    if type(Value) is not int or not -(1 << 31) <= Value < (1 << 31) or Value == 0:
        raise BodyUnsupported("drawing detailing index requires nonzero downstream ids")
    return Value & 0xFFFFFFFF
