from ntpath import normcase as NormCase, normpath as NormPath
from convert.adapters.solidworks.Archive.Construction.NestedAssemblies.TargetPlacement import (
    TargetPlacement,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey


# different generated definitions must never collapse onto one native filename while repeated placements remain shared actual targets
def CheckDocPaths(Placements: tuple[TargetPlacement, ...], ParentPath: str) -> None:
    OwnersValue: dict[str, int] = {}
    SeenValues: set[int] = set()
    Pending = [ItemValue.TargetValue for ItemValue in Placements]
    ParentKey = NormCase(NormPath(ParentPath))
    while Pending:
        TargetValue = Pending.pop()
        IdentityValue = id(TargetValue.RootValue)
        FileValue = ArchiveNode.RequireNode(TargetValue.HeaderValue.FieldsValue["f38"])
        FileKey = NormCase(NormPath(ReadFileKey(FileValue)[1]))
        if FileKey == ParentKey or (
            FileKey in OwnersValue and OwnersValue[FileKey] != IdentityValue
        ):
            raise ValueError(
                "generated definition paths must be unique and exclude their containing output"
            )
        OwnersValue[FileKey] = IdentityValue
        if IdentityValue not in SeenValues:
            SeenValues.add(IdentityValue)
            Pending.extend(TargetValue.ChildTargets)
