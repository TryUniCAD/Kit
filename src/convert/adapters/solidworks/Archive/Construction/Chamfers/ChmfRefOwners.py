from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeSharedCopy import (
    MakeSharedCopy,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import (
    ChmfFaceRole,
)
from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import (
    MakeFileConfig,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)


# references couple an actual owners persistent id and retained creation event
@DataClass(frozen=True, slots=True)
class ChmfRefOwner:
    FeatureValue: ArchiveNode
    Identity: int
    SavedAt: int


# all local edge representatives have their own runtime object identity
def MakeChmfNode(ClassName: str, FieldsValue: dict[str, object]) -> ArchiveNode:
    return ArchiveNode(RuntimeClass(ClassName, 1), FieldsValue)


# a numbered owner needs the agreeing creation history of both newly generated headers
def ReadChmfOwner(StockValue: PartCandidate, FeatureValue: ArchiveNode) -> ChmfRefOwner:
    Identity = FieldInt(FeatureValue.FieldsValue, "f08")
    Config = DatumTime(StockValue.HeaderValue, Identity)
    TopTime = DatumTime(StockValue.TopHeader, Identity)
    if Identity <= 0 or Config != TopTime or Config == 2592000:
        raise ValueError("chamfer references need both actual feature creation events")
    return ChmfRefOwner(FeatureValue, Identity, Config)


# the historical surface file has its own allocated identity and the actual active self configuration
def MakeChmfFile(StockValue: PartCandidate) -> ArchiveNode:
    SelfFile = RequireNode(StockValue.HeaderValue.FieldsValue["f38"], "moExtObject_c")
    return MakeChmfNode(
        "moExtObject_c",
        {
            **dict.fromkeys(
                ("f48", "f4c", "f50", "f54", "f58", "f60", "f70", "f78"), 0
            ),
            "refcfg": MakeFileConfig(
                StockValue.SystemValue.RootValue, StockValue.CurrentConfig
            ),
            "shared": MakeSharedCopy(SelfFile),
        },
    )


# direct result and historical producer references preserve distinct live slots
def MakeChmfSurface(
    ClassName: str,
    OwnerValue: ChmfRefOwner,
    FileValue: ArchiveNode,
    ExtraValue: dict[str, object],
    DirectValue: bool,
) -> ArchiveNode:
    Reference = MakeChmfNode(
        "moFR_c",
        {
            "f08": FileValue,
            "f10": {"f00": OwnerValue.Identity, "f08": OwnerValue.SavedAt},
        },
    )
    return MakeChmfNode(
        ClassName,
        {
            "f10": {
                "f08": OwnerValue.FeatureValue if DirectValue else None,
                "f10": Reference,
            },
            **ExtraValue,
        },
    )


# cap references use the oriented cap slot while side references use the actual profile segment
def MakeChmfCarrier(
    RoleValue: ChmfFaceRole,
    OwnerValue: ChmfRefOwner,
    FileValue: ArchiveNode,
) -> ArchiveNode:
    if RoleValue.IsCap:
        return MakeChmfSurface(
            "moEndFaceSurfIdRep_c",
            OwnerValue,
            FileValue,
            {"f38": RoleValue.NumberValue, "f3c": 0},
            False,
        )
    return MakeChmfSurface(
        "moFromSktEntSurfIdRep_c",
        OwnerValue,
        FileValue,
        {"f38": RoleValue.NumberValue},
        False,
    )


# all keepers and the atom manager must resolve the same original stock row
def CheckChmfAtom(
    StockValue: PartCandidate, FeatureValue: ArchiveNode, AtomValue: ArchiveNode
) -> None:
    Model = StockValue.SystemValue.RootValue
    BossValue = StockValue.BossValue.FeatureValue
    (StockRow,) = ReadRows(RequireRecord(BossValue.FieldsValue["f528"])["items"])
    (ModelRow,) = ReadRows(RequireRecord(Model.FieldsValue["fd88"])["atoms"])
    if (
        FeatureValue.FieldsValue.get("owner") is not Model
        or FieldInt(FeatureValue.FieldsValue, "f08")
        == FieldInt(BossValue.FieldsValue, "f08")
        or AtomValue.FieldsValue["f12c"] != BossValue.FieldsValue["f08"]
        or AtomValue.FieldsValue["f130"] != FeatureValue.FieldsValue["f08"]
        or StockRow["o"] is not AtomValue
        or ModelRow["o"] is not AtomValue
        or FeatureValue.FieldsValue["f538"] is not AtomValue
    ):
        raise ValueError(
            "chamfer keeper requires the same producing stock and live modification atom"
        )
