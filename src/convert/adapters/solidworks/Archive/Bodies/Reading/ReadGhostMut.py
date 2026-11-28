from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion
from convert.adapters.solidworks.Archive.Reading.ReadNativeScalar import ReadScalarMut

from convert.adapters.solidworks.Archive.Bodies.Fields.GhostWord import (
    KGhostShift,
    KGhostCountMask,
    KGhostWordKind,
)


# signed high bits retain the ghost manager flags while low bits govern row count
def ReadGhostMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if FrameValue.ContextValue.VersionValue != KHeaderVersion:
        raise BodyUnsupported("SOLIDWORKS ghost count requires archive version 19000")
    Packed = CastValue(
        int, ReadScalarMut(FrameValue.ReaderValue.Cursor, KGhostWordKind)
    )
    Fields = FrameValue.ScopeValue.FieldsValue
    Fields[RuleValue.OtherName] = Packed >> KGhostShift
    Fields[RuleValue.NameValue] = Packed & KGhostCountMask
