from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass


def ReadLineage(
    Classes: tuple[MetaClass, ...], ClassGuid: str
) -> tuple[ClassStamp, ...]:
    Registry = {Value.ClassGuid.upper(): Value for Value in Classes}
    Result: list[ClassStamp] = []
    Seen: set[str] = set()
    while ClassGuid:
        Identity = ClassGuid.upper()
        assert Identity not in Seen
        Seen.add(Identity)
        Value = Registry[Identity]
        Result.append(ClassStamp(Value.ClassGuid, Value.BaseGuid, Value.SchemaVersion))
        ClassGuid = Value.BaseGuid
    return tuple(Result)
