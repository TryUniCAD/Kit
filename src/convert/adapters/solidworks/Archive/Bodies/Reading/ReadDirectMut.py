from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Direct.DirectOwners import (
    KDirectOwners as KDirectOwners,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Maps.BindNodesMut import BindNodesMut


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
