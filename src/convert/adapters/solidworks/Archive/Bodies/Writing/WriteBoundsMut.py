from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# populated bounds need their own typed owners before the archive can encode a cache
def WriteBoundsMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    if ReadBodyRows(FrameValue.ScopeValue, RuleValue.NameValue):
        raise BodyUnsupported(
            "populated SOLIDWORKS part bounds cache requires typed owners"
        )
    FrameValue.WriterValue.OutputValue.extend(EncodeScalar(0, "i32"))
