from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadActions import KReadActions


# every admitted field operation needs a concrete implementation and an explicit unsupported outcome
def ReadFieldMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Handler = KReadActions.get(RuleValue.KindValue)
    if Handler is None:
        raise BodyUnsupported(
            f"unsupported SOLIDWORKS native field path {RuleValue.NameValue}"
        )
    Handler(FrameValue, RuleValue)
