from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteActions import (
    KWriteActions,
)


# each emitted field follows declared grammar without an opaque or recorded operation fallback
def WriteFieldMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Handler = KWriteActions.get(RuleValue.KindValue)
    if Handler is None:
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS native field path {RuleValue.NameValue}"
        )
    Handler(FrameValue, RuleValue)
