from dataclasses import dataclass as DataClass, field as FieldValue
from ntpath import normcase as NormCase, normpath as NormPath

from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey


# completed definitions and physical locators are validated once per generated bundle
@DataClass(slots=True)
class TargetAudit:
    Targets: dict[int, TargetDocument] = FieldValue(
        default_factory=dict[int, TargetDocument]
    )
    PathsValue: dict[str, int] = FieldValue(default_factory=dict[str, int])

    # different generated roots must never own the same native locator
    def StoreTargetMut(self, TargetValue: TargetDocument) -> None:
        FileValue = ArchiveNode.RequireNode(TargetValue.HeaderValue.FieldsValue["f38"])
        FileKey = NormCase(NormPath(ReadFileKey(FileValue)[1]))
        RootId = id(TargetValue.RootValue)
        if self.PathsValue.setdefault(FileKey, RootId) != RootId:
            raise ValueError("generated definition paths must be unique")
        self.Targets[id(TargetValue)] = TargetValue

    # verify the new output is distinct before constructing its assembly root
    def CheckParent(self, ParentPath: str) -> None:
        if NormCase(NormPath(ParentPath)) in self.PathsValue:
            raise ValueError(
                "generated definitions must exclude their containing output"
            )
