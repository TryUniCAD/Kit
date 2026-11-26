from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.ReadFrame import ReadFrame
from convert.adapters.solidworks.Archive.Bodies.Reading.ReadCacheNumMut import (
    ReadCacheNumMut,
)


# the observed bounds cache can complete only before any key and object rows appear
def ReadBBoxMut(FrameValue: ReadFrame, RuleValue: NativeField) -> None:
    if ReadCacheNumMut(FrameValue.ReaderValue.Cursor):
        raise BodyUnsupported(
            "populated SOLIDWORKS part bounds cache requires typed owners"
        )
    FrameValue.ScopeValue.FieldsValue[RuleValue.NameValue] = []
