from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# native counters and clocks must retain integer types before their semantic domains are checked
def Integer(Value: object) -> int:
    if type(Value) is not int:
        raise BodyUnsupported("blank integer owner has another type")
    return Value
