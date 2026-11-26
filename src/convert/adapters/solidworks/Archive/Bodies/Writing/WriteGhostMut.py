from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadBodyRows import ReadBodyRows
from convert.adapters.solidworks.Archive.Bodies.ReadScopeValue import ReadScopeValue
from convert.adapters.solidworks.Archive.Bodies.WriteFrame import WriteFrame
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar


# the packed ghost word keeps the signed flag independent of the actual row count
def WriteGhostMut(FrameValue: WriteFrame, RuleValue: NativeField) -> None:
    Writer = FrameValue.WriterValue
    if Writer.ContextValue.VersionValue != KHeaderVersion:
        raise BodyUnsupported("SOLIDWORKS ghost count requires archive version 19000")
    Scope = FrameValue.ScopeValue
    Count = len(ReadBodyRows(Scope, RuleValue.CountValue))
    if Count != 0:
        raise BodyUnsupported("unqualified populated SOLIDWORKS ghost rows")
    Flags = ReadScopeValue(Scope, RuleValue.OtherName)
    if type(Flags) is not int or not -8 <= Flags <= 7:
        raise ValueError("native ghost flags require a signed four bit integer")
    Writer.OutputValue.extend(EncodeScalar((Flags << 28) | Count, "i32"))
    Scope.ValuesValue[RuleValue.NameValue] = Count
