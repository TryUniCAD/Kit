from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TrackAttrib import TrackAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadFdmAttrib import (
    ReadFdmAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadTagGroups import (
    ReadTagGroups,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadSourceLink import (
    ReadSourceLink,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)


def ReadAttribNode(Cursor: FieldCursor) -> KJournalEntity:
    NeedFieldMut(Cursor, (12, -1))
    NeedFieldMut(Cursor, (4, -1))
    Links = AttribLinks(ReadRefMut(Cursor), ReadRefMut(Cursor), ReadRefMut(Cursor))
    Family = ReadTextMut(Cursor)
    if Family == "generic_tag_attrib_def":
        return TagAttrib(Links, ReadTagGroups(Cursor))
    if Family == "sketch_attrib_def":
        return SketchAttrib(Links, ReadSourceLink(Cursor))
    if Family in ("Timestamp_attrib_def", "FPM_tracked_attrib_def"):
        NeedFieldMut(Cursor, (4, 1))
        return (
            TimeAttrib(Links, ReadDoubleMut(Cursor))
            if Family == "Timestamp_attrib_def"
            else TrackAttrib(Links, ReadLongMut(Cursor))
        )
    if Family == "FDM_feature_attrib_def":
        return ReadFdmAttrib(Cursor, Links)
    raise ValueError("Unsupported Fusion journal attribute family")
