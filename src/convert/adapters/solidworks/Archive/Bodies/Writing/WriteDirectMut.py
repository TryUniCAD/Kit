from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut


# model emission must reserve header aliases using the same derived counter and object identities
def WriteDirectMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    if FrameValue.NodeValue.ClassValue.NameValue == "moDrawing_c":
        raise BodyUnsupported(
            "ordinary configuration graph excludes inline drawing headers"
        )
    BindNodesMut(
        FrameValue.WriterValue.MapValue, FrameValue.WriterValue.ContextValue.DirectNodes
    )
