from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Model.MakeModelSeeds import (
    MakeModelSeeds,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeGhostWorld import (
    MakeGhostWorld,
)
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeSwSheet import MakeSwSheet
from convert.adapters.solidworks.Archive.Partition.Sweeps.MakeSwWire import MakeSwWire
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireRecord,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.SweepIntent import SweepIntent


# both picked ghost identities remain linked to the actual generated ghost partition and part manager
@DataClass(frozen=True, slots=True)
class SweepGhostPair:
    SectionId: int
    PathId: int
    ManagerValue: dict[str, object]
    StreamValue: bytes


# a sweep owns the next two fresh identities of the actual part ghost manager
def MakeGhostRows(
    PartValue: ArchiveNode, SweepValue: ArchiveNode
) -> tuple[int, int, dict[str, object]]:
    ManagerValue = RequireRecord(PartValue.FieldsValue["fd90"])
    SeedValue = RequireRecord(MakeModelSeeds()["fd90"])
    Identifier = FieldInt(SweepValue.FieldsValue, "f08")
    if (
        PartValue.ClassValue != RuntimeClass("moPart_c", 1)
        or SweepValue.ClassValue != RuntimeClass("moSweep_c", 1)
        or SweepValue.FieldsValue.get("owner") is not PartValue
        or not 0 < Identifier < 0x7FFFFFFF
        or ManagerValue.keys() != SeedValue.keys()
        or FieldInt(ManagerValue, "f80") != FieldInt(SeedValue, "f80")
        or any(FieldInt(ManagerValue, NameValue) for NameValue in ("fe0", "n"))
        or ReadRows(ManagerValue["objects"])
    ):
        raise ValueError(
            "sweep ghost construction requires its actual part and fresh empty manager"
        )
    SectionId = FieldInt(ManagerValue, "f80") + 1
    PathId = SectionId + 1
    GhostRows = tuple(
        {
            "o": {
                "f08": NodeId,
                "f0c": 8,
                "f10": 0,
                "fc0": -1,
                "fa0": ({"v": Identifier},),
                "has_f50": 0,
                "ff0": (),
            }
        }
        for NodeId in (PathId, SectionId)
    )
    return (
        SectionId,
        PathId,
        {"f80": PathId, "fe0": len(GhostRows), "objects": GhostRows},
    )


# ghost shape paths derive from the same authored circle and arc used for the live editable sketches
def MakeGhostPair(
    PartValue: ArchiveNode, SweepValue: ArchiveNode, IntentValue: SweepIntent
) -> SweepGhostPair:
    SectionId, PathId, ManagerValue = MakeGhostRows(PartValue, SweepValue)
    SheetValue = MakeSwSheet(IntentValue.SectionValue)
    WireValue = MakeSwWire(IntentValue.PathValue)
    return SweepGhostPair(
        SectionId,
        PathId,
        ManagerValue,
        MakeGhostWorld(SheetValue, WireValue, SectionId, PathId),
    )
