from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.CheckStockFace import (
    CheckStockFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRef import (
    ReadStockRef,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the immediate selected atom and base producer require separate graph evidence
def CheckPatPick(
    LinkValue: NativeLink,
    FeatureValue: ArchiveNode,
    PlateValue: ArchiveNode,
    AtomIds: tuple[int, ...],
) -> ArchiveNode:
    Fields = FeatureValue.FieldsValue
    Wrapped = ReadSingleNode(Fields.get("f548"), "moCompSolidBody_c")
    Members = Wrapped.FieldsValue
    Component = RequireNative(Members.get("f58"), "moUnitComponent_c")
    FaceValue = RequireNative(Members.get("ff0"), "moFaceRef_c")
    CheckTreeAlias(LinkValue, (Wrapped, Component, FaceValue))
    if (
        Fields.get("f544") != 1
        or Fields.get("has_f548") != 1
        or Members.get("f18") != AtomIds[0]
        or Members.get("f1c") != AtomIds[0]
        or Members.get("f108") != NativeNodeId(PlateValue)
        or Members.get("n110") != len(AtomIds)
        or tuple(RowValue.get("v") for RowValue in NativeRows(Members.get("f110")))
        != AtomIds
        or Members.get("f100") != 0
        or Members.get("f104") != 0
        or Component.FieldsValue.get("owner") is not LinkValue.ConfigValue.RootValue
        or Component.FieldsValue.get("has_ext") != 0
    ):
        raise ValueError(
            "pattern scope does not identify its consumed local body lineage"
        )
    if len(AtomIds) == 1:
        CheckStockFace(Wrapped, PlateValue)
    return ReadStockRef(
        FaceValue, PlateValue, 3 if len(AtomIds) == 1 else 4, LinkValue=LinkValue
    )
