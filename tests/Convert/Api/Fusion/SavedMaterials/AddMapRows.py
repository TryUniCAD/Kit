from dataclasses import replace as ReplaceData
from uuid import UUID as UuidValue

from convert.Formats.Fusion.DocumentCodec.DraftDesign import DraftDesign
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DocumentCodec.Records.DraftRecords import DraftRecords
from tests.Convert.Api.Fusion.SavedMaterials.StageMapDraft import StageMapDraft


# append only independently drafted scene rows and their allocated class owners to the fixture
def AddMapRows(Design: ParsedSegment) -> tuple[ParsedSegment, int]:
    SpecValue = DocumentSpec(
        "Mapping test",
        "heightEdit",
        27.0,
        "cuboid",
        WidthMm=18.0,
        DepthMm=22.0,
        ConstrainRectangle=True,
    )
    Author = DraftDesign(SpecValue, str(UuidValue(int=57)))
    Author.NextId = Design.Metadata.NextId
    StageMapDraft(Author)
    Codes = {
        ClassRow.ClassGuid.upper(): 256 + Index
        for Index, ClassRow in enumerate(Design.Metadata.Classes)
    }
    MappingIds = {
        Value
        for NameValue, Value in Author.Roles.items()
        if NameValue.startswith("mapping_")
    }
    Added = tuple(
        Record
        for Record in DraftRecords(Author, Codes)
        if Record.ObjectId in MappingIds
    )
    assert len(Added) == 3 and all(Record.IsPrimary for Record in Added)
    Owners = {Record.Groups[0].ClassGuid.upper(): Record.ObjectId for Record in Added}
    Classes = tuple(
        (
            ReplaceData(
                ClassRow,
                OwnerIds=(*ClassRow.OwnerIds, Owners[ClassRow.ClassGuid.upper()]),
            )
            if ClassRow.ClassGuid.upper() in Owners
            else ClassRow
        )
        for ClassRow in Design.Metadata.Classes
    )
    MetaValue = ReplaceData(Design.Metadata, NextId=Author.NextId, Classes=Classes)
    return (
        ReplaceData(Design, Records=(*Design.Records, *Added), Metadata=MetaValue),
        Author.Roles["mapping_layers"],
    )
