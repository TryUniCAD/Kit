from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the primary component edge must alias the keeper while the extra edge keeps its separate identity
def ReadChmfPick(
    LinkValue: NativeLink, FeatureValue: ArchiveNode, AtomId: int
) -> tuple[ArchiveNode, ArchiveNode]:
    Fields = FeatureValue.FieldsValue
    Selected = RequireNative(Fields.get("f888"), "suObList")
    (PickedRow,) = NativeRows(Selected.FieldsValue["items"])
    Picked = RequireNative(PickedRow.get("o"), "moCompEdge_c")
    OtherEdge = RequireNative(Fields.get("f8a8"), "moCompEdge_c")
    Keeper = NativeRecord(Fields.get("f880"))
    (KeeperRow,) = NativeRows(NativeRecord(Keeper.get("ff0")).get("items"))
    References = (
        RequireNative(Picked.FieldsValue.get("fe8"), "moEdgeRef_c"),
        RequireNative(OtherEdge.FieldsValue.get("fe8"), "moEdgeRef_c"),
    )
    PrimaryKey = References[0].FieldsValue.get("f70")
    if (
        Picked is OtherEdge
        or References[0] is References[1]
        or KeeperRow.get("o") is not References[0]
        or type(PrimaryKey) is not int
        or PrimaryKey <= 0
        or References[1].FieldsValue.get("f70") != 0
        or any(
            NodeValue.FieldsValue.get("f18") != AtomId
            or NodeValue.FieldsValue.get("f1c") != AtomId
            or NodeValue.FieldsValue.get("ff0") is not None
            or NodeValue.FieldsValue.get("n140") != 0
            for NodeValue in (Picked, OtherEdge)
        )
        or any(
            NodeValue.FieldsValue.get("f08")
            != len(NativeRows(NodeValue.FieldsValue.get("f10")))
            or NodeValue.FieldsValue.get("f08") != 4
            or NodeValue.FieldsValue.get("fe8") != 512
            or NodeValue.FieldsValue.get("f60") != 1
            or NodeValue.FieldsValue.get("f64") != 0
            or NodeValue.FieldsValue.get("f48") != 0
            or NodeValue.FieldsValue.get("has_f18") != 0
            or NodeValue.FieldsValue.get("nd0") != 0
            for NodeValue in References
        )
    ):
        raise ValueError("ordinary chamfer has conflicting selected edge ownership")
    CheckTreeAlias(LinkValue, (Selected, Picked, OtherEdge, *References))
    return References
