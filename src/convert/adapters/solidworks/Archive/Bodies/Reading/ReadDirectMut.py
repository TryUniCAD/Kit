from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# ordinary model headers register direct aliases only in their concrete root roles
KDirectOwners = (RuntimeClass("moPart_c", 1), RuntimeClass("moAssembly_c", 1))


# registering selected header objects changes the inherited base without consuming bytes
def ReadDirectMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    Context = FrameValue.ContextValue
    if (
        Context.VersionValue != KHeaderVersion
        or FrameValue.NodeValue.ClassValue not in KDirectOwners
        or FrameValue.ScopeValue.ParentValue is not None
    ):
        raise BodyUnsupported("unsupported SOLIDWORKS direct model header owner")
    BindNodesMut(FrameValue.ReaderValue.MapValue, Context.DirectNodes)
