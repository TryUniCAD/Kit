from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeStockAtom import (
    MakeStockAtom,
)
from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# an ordinary local import must register one actual body atom and its own activation and selected marks
def BindImportMut(
    SystemValue: PartSystem,
    Allocator: PersistentIds,
    TargetValue: FeatureTarget,
    NameValue: str,
    MarkIds: tuple[int, int],
) -> tuple[ArchiveNode, int]:
    OwnerValue = SystemValue.RootValue
    RequireRootNode(OwnerValue, "moPart_c")
    RootFields = OwnerValue.FieldsValue
    ManagerValue = CastValue(dict[str, object], RootFields["fd88"])
    ConfigFields = SystemValue.ManagerValue.FieldsValue
    CursorValue = ManagerValue.get("f260")
    if (
        TargetValue.FileVersion != 19000
        or any(type(MarkId) is not int for MarkId in MarkIds)
        or not 0 < MarkIds[0] < MarkIds[1] < (1 << 31)
        or type(CursorValue) is not int
        or not 0 <= CursorValue < (1 << 31) - 1
        or ManagerValue.get("n6c") != 0
        or ManagerValue.get("atoms")
        or RootFields.get("fe38") is not None
        or RootFields.get("f1010")
        or ConfigFields.get("f658") != 0
    ):
        raise ValueError("local import needs a fresh part and two valid marks")
    FeatureValue = ArchiveNode(RuntimeClass("moBaseBody_c", 1), {})
    InitFeatureMut(FeatureValue, NameValue, OwnerValue, TargetValue, Allocator)
    FieldsValue = FeatureValue.FieldsValue
    FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    FieldsValue.update({FieldName: [] for FieldName in KAtomLists})
    FieldsValue.update(
        f35c=0,
        f368={"n": 0, "items": []},
        f388={"n": 0, "items": []},
        f538=None,
        f4a0=1,
        f6e0=None,
        f758=None,
        f780={"n": 0, "items": []},
        f7a0=0,
        source_filename="",
        local_body_switch=1,
        local_storage_key=NameValue,
        segment_mesh_count=0,
        segment_mesh_ids=[],
    )
    AtomId = CursorValue + 1
    AtomValue = MakeStockAtom(FeatureValue, AtomId)
    AtomValue.FieldsValue["f188"] = 1
    Entries = [{"o": AtomValue}]
    Activation, Selected = (
        ArchiveNode(RuntimeClass("moPMarkRecord_c", 1), {"f18": MarkId})
        for MarkId in MarkIds
    )
    ManagerValue.update(f260=AtomId, n6c=len(Entries), atoms=Entries, fa8=19000)
    ConfigFields["f658"] = 1
    RootFields.update(fe38=Activation, f1010=1)
    FieldsValue.update(
        has_f528=1,
        f528={"n": len(Entries), "items": Entries},
        n494=len(Entries),
        f498=[{"v": AtomId}],
        has_f3d0=1,
        f3d0=Selected,
        f3c0=0,
        f3c8=0,
        f580=0,
    )
    return FeatureValue, AtomId
