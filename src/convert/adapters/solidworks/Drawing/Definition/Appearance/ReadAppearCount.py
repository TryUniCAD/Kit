from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported


# native allocator halves require their signed wire domain before unsigned reconstruction
def NeedAppearLong(Value: object) -> int:
    if type(Value) is not int or not -(1 << 31) <= Value < (1 << 31):
        raise BodyUnsupported("drawing appearance allocator requires signed32 words")
    return Value


# allocation history survives semantic reading without replacement by a fresh constructor seed
def ReadAppearCount(FieldsValue: Mapping[str, object]) -> int:
    LowValue = NeedAppearLong(FieldsValue["f08"])
    HighValue = NeedAppearLong(FieldsValue["f0c"])
    return (LowValue & 0xFFFFFFFF) | ((HighValue & 0xFFFFFFFF) << 32)
