from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut


# configuration prefixes must bind the exact header objects after the model root is allocated
def ReadDirectMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if FrameValue.NodeValue.ClassValue.NameValue == "moDrawing_c":
        raise BodyUnsupported(
            "ordinary configuration graph excludes inline drawing headers"
        )
    BindNodesMut(FrameValue.ReaderValue.MapValue, FrameValue.ContextValue.DirectNodes)
