from pathlib import PurePosixPath as AssetPath

from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


# inspect physical primary groups so a merged node cannot hide a continuation
def CheckConfRoots(Model: DocumentModel, Parts: tuple[tuple[str, str], ...]) -> None:
    (Design,) = tuple(
        Segment for Segment in Model.Segments if Segment.Metadata.Header.SegmentId == 0
    )
    for RoleName in ("table", "rule"):
        RootName = f"DesignConfiguration{RoleName.title()}SerializerTrigger"
        Known = tuple(
            NameValue for PartRole, NameValue in Parts if PartRole == RoleName
        )
        Roots = tuple(
            Entry for Entry in Design.Records if Entry.Frame.RootId == RootName
        )
        assert len(Roots) == len(Known)
        for Owner, NameValue in zip(Roots, Known, strict=True):
            assert Owner.IsPrimary and len(Owner.Groups) == 2
            assert (
                sum(Entry.ObjectId == Owner.ObjectId for Entry in Design.Records) == 1
            )
            First, Second = Owner.Groups
            assert not First.Fields
            assert tuple((Field.FieldName, Field.Value) for Field in Second.Fields) == (
                ("partName", AssetPath(NameValue).name),
            )
