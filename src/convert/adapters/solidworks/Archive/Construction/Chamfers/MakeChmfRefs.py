from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfEdgeRoles import (
    KChmfSupports,
)
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfRefOwners import (
    CheckChmfAtom,
    MakeChmfCarrier,
    MakeChmfFile,
    MakeChmfNode,
    MakeChmfSurface,
    ReadChmfOwner,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import (
    MakeObList,
)
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import (
    MakeSelfComp,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# fresh reference corners reconstruct their unassigned live tag from typed surface ownership on load
def MakeChmfEdge(
    SupportValue: tuple[ArchiveNode, ...],
    AtomId: int,
    ModelValue: ArchiveNode,
) -> tuple[ArchiveNode, ArchiveNode]:
    Reference = MakeChmfNode(
        "moEdgeRef_c",
        {
            "f60": 1,
            "f64": 0,
            "f08": len(SupportValue),
            "fe8": 0x200,
            "f70": 0,
            "f28": 1e100,
            "f30": 1e100,
            "f40": None,
            "f10": [{"f08": Surface} for Surface in SupportValue],
            "f48": 0,
            "nd0": 0,
            "fd0": [],
            "fec": 19000,
            "has_f18": 0,
        },
    )
    Fields = CompRefFields(MakeSelfComp(ModelValue))
    Fields.update(
        f18=AtomId,
        f1c=AtomId,
        has_alias=0,
        fe8=Reference,
        ff0=None,
        f188=0,
        f158=dict.fromkeys("xyz", 0.0),
        f170=dict.fromkeys("xyz", 0.0),
        f18c=0,
        n140=0,
        f130=[],
    )
    Wrapper = MakeChmfNode("moCompEdge_c", Fields)
    return Wrapper, Reference


# the owned selection and detached reference allocate separate wrappers with the same actual signed carriers
def MakeChmfRefs(
    StockValue: PartCandidate,
    FeatureValue: ArchiveNode,
    AtomValue: ArchiveNode,
    Roles: KChmfSupports,
) -> dict[str, object]:
    CheckChmfAtom(StockValue, FeatureValue, AtomValue)
    ModelValue = StockValue.SystemValue.RootValue
    BossOwner = ReadChmfOwner(StockValue, StockValue.BossValue.FeatureValue)
    ChmfOwner = ReadChmfOwner(StockValue, FeatureValue)
    FileValue = MakeChmfFile(StockValue)
    AtomId = FieldInt(AtomValue.FieldsValue, "f140")
    Selected, Primary = MakeChmfEdge(
        tuple(MakeChmfCarrier(RoleValue, BossOwner, FileValue) for RoleValue in Roles),
        AtomId,
        ModelValue,
    )
    Detached, _ = MakeChmfEdge(
        tuple(MakeChmfCarrier(RoleValue, BossOwner, FileValue) for RoleValue in Roles),
        AtomId,
        ModelValue,
    )
    Surfaces = (
        MakeChmfSurface("moSurfaceIdRep_c", ChmfOwner, FileValue, {}, True),
        MakeChmfSurface("moFilletSurfIdRep_c", ChmfOwner, FileValue, {"f38": 1}, True),
    )
    Keeper = {
        "f18": {
            "n": len(Surfaces),
            "items": [{"id": {"f08": Surface}} for Surface in Surfaces],
        },
        "ff0": {"n": 1, "items": [{"o": Primary}]},
    }
    return {
        "f880": Keeper,
        "f888": MakeChmfNode("suObList", {"n": 1, "items": [{"o": Selected}]}),
        "f890": MakeChmfNode("suObList", MakeObList()),
        "f898": MakeChmfNode("suObList", MakeObList()),
        "f8a8": Detached,
    }
