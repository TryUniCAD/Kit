from json import loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment


# design graph labels apply only when the saved class version and base agree with the reflected identity
def DesignNames(Segment: ParsedSegment) -> dict[str, str]:
    if Segment.Metadata.Header.SegmentId != 0:
        return {}
    Names = CastValue(
        dict[str, list[object]],
        LoadJson(FilePath(__file__).with_suffix(".json").read_bytes()),
    )
    Result: dict[str, str] = {}
    for Entry in Segment.Metadata.Classes:
        Guid = Entry.ClassGuid.upper()
        Row = Names.get(Guid)
        if Row and Row[1:] == [
            Entry.SchemaVersion,
            Entry.BaseGuid.upper(),
            Entry.ClassSpace,
        ]:
            Result[Guid] = str(Row[0])
    return Result
